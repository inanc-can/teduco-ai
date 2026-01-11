"""
Agentic RAG assistant

This module provides an Agent class that can:
- Plan whether to consult user profile and user documents
- Fetch user profile and documents from Supabase
- Search both the global vector store and user documents (embeddings)
- Produce a short, precise answer using only Groq models (ChatGroq)

The design minimizes changes to the frontend: the /chat endpoint may optionally include
an Authorization header. When a user is authenticated the agent will incorporate
user-specific data automatically.
"""

import json
import os
import requests
import traceback
from typing import List, Optional, Dict, Any
from io import BytesIO

import numpy as np
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from db.lib import core as db_core
from core.dependencies import get_signed_url

# Try to import PDF parser for document processing
try:
    from rag.parser.conversion import DoclingPDFParser
    PDF_PARSER_AVAILABLE = True
except ImportError:
    PDF_PARSER_AVAILABLE = False
    print("[Agent] Warning: DoclingPDFParser not available. PDF documents will be skipped.")


class Agent:
    def __init__(
        self,
        llm: ChatGroq,
        retriever_pipeline,
        embeddings,
        k: int = 3,
        similarity_threshold: float = 0.40,
    ):
        self.llm = llm
        self.retriever_pipeline = retriever_pipeline
        self.embeddings = embeddings
        self.k = k
        self.similarity_threshold = similarity_threshold

        # Setup requests session with USER_AGENT header (fallback default provided)
        self.session = requests.Session()
        ua = os.getenv("USER_AGENT", "teduco-backend/0.1")
        self.session.headers.update({"User-Agent": ua})

    # ------------------ Planning ------------------
    def plan_actions(self, question: str, user_profile_summary: Optional[str] = None) -> List[str]:
        """Ask the LLM to decide which actions are necessary.
        Returns a list of actions (strings) in lower case.

        Possible actions:
          - fetch_profile
          - fetch_user_docs
          - search_kb
          - search_user_docs
          - answer
        """
        planner_prompt = (
            "You are a planner. Given a user question and an optional short user profile summary, "
            "decide which of the following actions are needed to answer the question correctly and concisely: "
            "[fetch_profile, fetch_user_docs, search_kb, search_user_docs, answer].\n"
            "Output a JSON object with a single key 'actions' whose value is an ordered list of actions. "
            'Only include actions that are necessary. Example: {"actions": ["search_kb","answer"]}\n'
            "User profile summary (if available):\n" + (user_profile_summary or "None") + "\n"
            "Question:\n" + question + "\n"
        )

        try:
            # Use invoke() with HumanMessage
            resp = self.llm.invoke([
                HumanMessage(content=planner_prompt)
            ], temperature=0)
        except Exception:
            # Fallback: simple heuristic
            if any(word in question.lower() for word in ["my", "me", "i ", "profile", "documents", "transcript"]):
                return ["fetch_profile", "search_user_docs", "search_kb", "answer"]
            return ["search_kb", "answer"]

        # Try to parse JSON from the response content
        content = None
        if hasattr(resp, 'content'):
            content = resp.content
        elif isinstance(resp, dict):
            content = resp.get("content")
        else:
            content = str(resp)

        try:
            parsed = json.loads(content)
            actions = parsed.get("actions", [])
            actions = [a.strip().lower() for a in actions]
            # Ensure KB is consulted for application/university questions
            ql = question.lower()
            must_kb_keywords = [
                "apply", "application", "admission", "requirements", "deadline",
                "university", "tum", "program", "degree", "eligible"
            ]
            if any(k in ql for k in must_kb_keywords):
                if "search_kb" not in actions:
                    actions.append("search_kb")
                if "answer" not in actions:
                    actions.append("answer")
            return actions
        except Exception:
            # Best-effort parse: look for keywords
            lc = content.lower() if isinstance(content, str) else ""
            actions = []
            for a in ["fetch_profile", "fetch_user_docs", "search_user_docs", "search_kb", "answer"]:
                if a in lc:
                    actions.append(a)
            if not actions:
                actions = ["search_kb", "answer"]
            # Enforce KB for application/university keywords
            ql = question.lower()
            must_kb_keywords = [
                "apply", "application", "admission", "requirements", "deadline",
                "university", "tum", "program", "degree", "eligible"
            ]
            if any(k in ql for k in must_kb_keywords) and "search_kb" not in actions:
                actions.append("search_kb")
            if "answer" not in actions:
                actions.append("answer")
            return actions

    # ------------------ Fetching ------------------
    def fetch_user_profile(self, user_id: str) -> Dict[str, Any]:
        try:
            profile = db_core.get_user_profile(user_id)
            return profile
        except Exception:
            traceback.print_exc()
            return {}

    # TODO: this part will be run by an enpoint of docling parser which will
    # rake pdf_bytes and return markdown str.
    def _parse_pdf_content(self, pdf_bytes: bytes, filename: str) -> Optional[str]:
        """Parse PDF content to text using Docling.
        
        Args:
            pdf_bytes: Raw PDF file content
            filename: Name of the file for logging
            
        Returns:
            Extracted text as markdown, or None if parsing fails
        """
        if not PDF_PARSER_AVAILABLE:
            print(f"[Agent] Skipping PDF {filename}: DoclingPDFParser not available")
            return None
        
        try:
            parser = DoclingPDFParser(force_full_page_ocr=False)
            conversion = parser.convert_document(pdf_bytes, name=filename)
            markdown_text = parser.conversion_to_markdown(conversion)
            if markdown_text and len(markdown_text.strip()) > 0:
                print(f"[Agent] ✓ Parsed PDF {filename}: {len(markdown_text)} chars")
                return markdown_text
        except Exception as e:
            print(f"[Agent] Failed to parse PDF {filename}: {e}")
        return None

    def fetch_user_documents(self, user_id: str) -> List[Document]:
        """Download user documents and return as a list of Document objects (page_content and metadata).
        
        Supports:
        - PDF files (CV, transcript, diploma) - parsed using Docling
        - Text-based files (txt, md) - read directly
        - Other formats are skipped
        """
        docs = []
        try:
            result = db_core.get_user_documents(user_id)
            if not result or not getattr(result, "data", None):
                print(f"[Agent] No documents found for user {user_id}")
                return []

            print(f"[Agent] Found {len(result.data)} documents for user {user_id}")

            for entry in result.data:
                storage_path = entry.get("storage_path")
                mime_type = entry.get("mime_type", "")
                doc_type = entry.get("doc_type", "other")
                
                if not storage_path:
                    continue
                    
                try:
                    url = get_signed_url(storage_path, expires_sec=120)
                    r = self.session.get(url, timeout=30)
                    if r.status_code != 200:
                        print(f"[Agent] Failed to download {storage_path}: HTTP {r.status_code}")
                        continue

                    text = None
                    
                    # Handle PDF files
                    if mime_type == "application/pdf" or storage_path.lower().endswith(".pdf"):
                        text = self._parse_pdf_content(r.content, storage_path.split("/")[-1])
                    
                    # Handle text-based files
                    elif mime_type in ["text/plain", "text/markdown"] or \
                         any(storage_path.lower().endswith(ext) for ext in [".txt", ".md"]):
                        try:
                            text = r.text
                        except Exception:
                            pass
                    
                    # Skip if no text extracted
                    if not text or len(text.strip()) == 0:
                        print(f"[Agent] No text extracted from {storage_path}")
                        continue

                    metadata = {
                        "source": "user_document",
                        "storage_path": storage_path,
                        "doc_type": doc_type,
                        "document_id": entry.get("document_id"),
                        "mime_type": mime_type,
                    }
                    docs.append(Document(page_content=text, metadata=metadata))
                    print(f"[Agent] ✓ Loaded document: {doc_type} ({len(text)} chars)")
                    
                except Exception as e:
                    print(f"[Agent] Error processing document {storage_path}: {e}")
                    traceback.print_exc()
                    continue
                    
        except Exception as e:
            print(f"[Agent] Error fetching user documents: {e}")
            traceback.print_exc()
            
        print(f"[Agent] Total documents loaded: {len(docs)}")
        return docs

    # ------------------ Search ------------------
    def search_kb(self, question: str) -> List[Document]:
        """Search the global vector store (the RAG KB) via similarity_search_with_score similar to the existing pipeline."""
        print(f"\n{'='*70}")
        print(f"[AGENT KB SEARCH] Searching knowledge base...")
        print(f"  Question: {question}")
        print(f"{'='*70}")
        
        try:
            vs = self.retriever_pipeline.vector_store
            print(f"[AGENT KB SEARCH] Vector store: {vs}")
            
            if vs is None:
                print("[AGENT KB SEARCH] ✗ Vector store is None!")
                print("[AGENT KB SEARCH] This means the FAISS index wasn't loaded properly.")
                print("[AGENT KB SEARCH] Check:")
                print("  1. Vector store path exists")
                print("  2. FAISS index was built during initialization")
                print("  3. retriever_pipeline.vector_store is set correctly")
                return []
            
            print(f"[AGENT KB SEARCH] Performing similarity search with k={self.k}...")
            results = vs.similarity_search_with_score(question, k=self.k)
            print(f"[AGENT KB SEARCH] Retrieved {len(results)} raw results")
            
            # Filter and log
            scored_filtered_docs = []
            for idx, (doc, score) in enumerate(results, 1):
                similarity = 1 / (1 + score)
                source = doc.metadata.get('source', 'unknown')
                section = doc.metadata.get('section', 'N/A')
                
                if similarity >= self.similarity_threshold:
                    print(f"[AGENT KB SEARCH]   [{idx}] ✓ Similarity: {similarity:.4f} - {source} - {section}")
                    scored_filtered_docs.append((doc, similarity))
                else:
                    print(f"[AGENT KB SEARCH]   [{idx}] ✗ Similarity: {similarity:.4f} (below {self.similarity_threshold}) - {source}")
            
            # Sort deterministically
            scored_filtered_docs.sort(key=lambda x: (-x[1], str(x[0].metadata.get('key', ''))))
            docs = [doc for doc, _sim in scored_filtered_docs]
            
            print(f"[AGENT KB SEARCH] ✓ Returning {len(docs)}/{len(results)} documents above threshold")
            print(f"{'='*70}\n")
            return docs
            
        except Exception as e:
            print(f"[AGENT KB SEARCH] ✗ Exception during search: {e}")
            traceback.print_exc()
            print(f"{'='*70}\n")
            return []

    def search_user_docs(self, question: str, user_docs: List[Document]) -> List[Document]:
        """
        Build a FAISS vector store from user docs and perform similarity search.
        Uses the same approach as KB search for consistency and determinism.
        """
        if not user_docs:
            return []
        try:
            print(f"[Agent] Building FAISS index for {len(user_docs)} user documents...")
            # Create a temporary FAISS vector store for user documents
            user_vector_store = FAISS.from_documents(
                documents=user_docs,
                embedding=self.embeddings
            )
            
            # Perform similarity search with scores (same as KB search)
            results_with_scores = user_vector_store.similarity_search_with_score(
                question,
                k=self.k
            )
            
            print(f"[Agent] User doc search returned {len(results_with_scores)} results")
            
            # Filter by threshold and sort deterministically
            scored_filtered_docs = []
            for doc, score in results_with_scores:
                # Convert L2 distance to similarity (same as KB retrieval)
                similarity = 1 / (1 + score)
                
                if similarity >= self.similarity_threshold:
                    scored_filtered_docs.append((doc, similarity))
                    print(f"[Agent] ✓ User doc similarity: {similarity:.4f} - {doc.metadata.get('doc_type', 'unknown')}")
                else:
                    print(f"[Agent] ✗ User doc similarity: {similarity:.4f} - below threshold {self.similarity_threshold}")
            
            # Sort deterministically by similarity (descending), then by doc_type
            scored_filtered_docs.sort(key=lambda x: (-x[1], str(x[0].metadata.get('doc_type', ''))))
            filtered_docs = [doc for doc, _sim in scored_filtered_docs]
            
            print(f"[Agent] Returning {len(filtered_docs)}/{len(results_with_scores)} user docs above threshold")
            return filtered_docs
            
        except Exception:
            print("[Agent] Error in search_user_docs:")
            traceback.print_exc()
            return []

    # ------------------ Final Answer ------------------
    def compile_context_text(self, profile: Dict[str, Any], kb_docs: List[Document], user_docs: List[Document]) -> str:
        """
        Compile all retrieved context into a structured text for the LLM.
        
        The context has 3 sections:
        1. USER PROFILE - Personal info from Supabase (name, education, GPA, preferences)
        2. USER DOCUMENTS - Content from uploaded files (CV, transcript, diploma)
        3. KB DOCUMENTS - Retrieved TUM program information from FAISS
        
        The agent should use USER PROFILE + USER DOCUMENTS to understand the user's background,
        and KB DOCUMENTS to provide accurate TUM-specific information.
        """
        print(f"\n{'='*70}")
        print("[AGENT CONTEXT DEBUG] Building context from available sources...")
        print(f"{'='*70}")
        
        parts = []
        
        # ============================================================
        # SECTION 1: USER PROFILE (from Supabase database tables)
        # This helps the agent understand WHO the user is
        # ============================================================
        if profile and profile.get("user"):
            print("[AGENT CONTEXT] ✓ USER PROFILE available")
            user = profile.get("user")
            profile_lines = []
            
            # Basic info
            if user.get("first_name") or user.get("last_name"):
                profile_lines.append(f"Name: {user.get('first_name', '')} {user.get('last_name', '')}".strip())
            if user.get("current_city"):
                profile_lines.append(f"Current City: {user.get('current_city')}")
            if user.get("applicant_type"):
                profile_lines.append(f"Applicant Type: {user.get('applicant_type')}")
            
            # Education details
            if profile.get("education"):
                edu = profile.get("education")
                edu_type = edu.get("type", "unknown")
                profile_lines.append(f"\n--- Education ({edu_type}) ---")
                
                if edu_type == "university":
                    if edu.get("university_name"):
                        profile_lines.append(f"University: {edu.get('university_name')}")
                    if edu.get("university_program"):
                        profile_lines.append(f"Current Program: {edu.get('university_program')}")
                    if edu.get("gpa"):
                        profile_lines.append(f"GPA: {edu.get('gpa')}")
                    if edu.get("credits_completed"):
                        profile_lines.append(f"Credits Completed: {edu.get('credits_completed')}")
                    if edu.get("expected_graduation"):
                        profile_lines.append(f"Expected Graduation: {edu.get('expected_graduation')}")
                    if edu.get("research_focus"):
                        profile_lines.append(f"Research Focus: {edu.get('research_focus')}")
                else:  # high school
                    if edu.get("high_school_name"):
                        profile_lines.append(f"High School: {edu.get('high_school_name')}")
                    if edu.get("gpa"):
                        profile_lines.append(f"GPA: {edu.get('gpa')}/{edu.get('gpa_scale', '4.0')}")
                    if edu.get("grad_year"):
                        profile_lines.append(f"Graduation Year: {edu.get('grad_year')}")
                    if edu.get("extracurriculars"):
                        profile_lines.append(f"Extracurriculars: {edu.get('extracurriculars')}")
            
            # Preferences (what they're looking for)
            if profile.get("preferences"):
                prefs = profile.get("preferences")
                profile_lines.append("\n--- Application Preferences ---")
                if prefs.get("desired_countries"):
                    profile_lines.append(f"Desired Countries: {', '.join(prefs.get('desired_countries', []))}")
                if prefs.get("desired_fields"):
                    profile_lines.append(f"Desired Fields: {', '.join(prefs.get('desired_fields', []))}")
                if prefs.get("target_programs"):
                    profile_lines.append(f"Target Programs: {', '.join(prefs.get('target_programs', []))}")
                if prefs.get("preferred_intake"):
                    profile_lines.append(f"Preferred Intake: {prefs.get('preferred_intake')}")
                if prefs.get("additional_notes"):
                    profile_lines.append(f"Additional Notes: {prefs.get('additional_notes')}")
            
            parts.append("=== USER PROFILE ===\n" + "\n".join(profile_lines))
        else:
            print("[AGENT CONTEXT] ✗ No USER PROFILE available")

        # ============================================================
        # SECTION 2: USER DOCUMENTS (CV, transcript, diploma from Supabase Storage)
        # This provides detailed background about the user's qualifications
        # ============================================================
        if user_docs:
            print(f"[AGENT CONTEXT] ✓ USER DOCUMENTS available ({len(user_docs)} docs)")
            doc_parts = []
            for d in user_docs[:self.k]:
                doc_type = d.metadata.get("doc_type", "document")
                # Include more content (up to 1500 chars) for better context
                content = d.page_content[:1500].replace("\n", " ").strip()
                doc_parts.append(f"[{doc_type.upper()}]: {content}")
            parts.append("=== USER DOCUMENTS ===\n" + "\n\n".join(doc_parts))
        else:
            print("[AGENT CONTEXT] ✗ No USER DOCUMENTS available")

        # ============================================================
        # SECTION 3: KB DOCUMENTS (TUM program info from FAISS vector store)
        # This is the ONLY source of truth for TUM-specific information
        # ============================================================
        if kb_docs:
            print(f"[AGENT CONTEXT] ✓ TUM KNOWLEDGE BASE available ({len(kb_docs)} docs)")
            kb_parts = []
            for d in kb_docs[:self.k]:
                source = d.metadata.get("source", "unknown")
                section = d.metadata.get("section", "")
                # Include more content for accurate answers
                content = d.page_content[:1500].replace("\n", " ").strip()
                kb_parts.append(f"[Source: {source}] {section}\n{content}")
            parts.append("=== TUM KNOWLEDGE BASE ===\n" + "\n\n".join(kb_parts))
        else:
            print("[AGENT CONTEXT] ✗ No TUM KNOWLEDGE BASE documents retrieved")

        context_text = "\n\n".join(parts) if parts else "No context available"
        
        print(f"\n{'='*70}")
        print("[AGENT CONTEXT DEBUG] Full context compiled:")
        print(f"{'='*70}")
        print(context_text)
        print(f"{'='*70}\n")
        
        return context_text

    def final_answer(self, question: str, profile: Dict[str, Any], kb_docs: List[Document], user_docs: List[Document], chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        print(f"\n{'='*70}")
        print("[AGENT] Generating final answer...")
        print(f"  Question: {question}")
        print(f"  Chat history length: {len(chat_history) if chat_history else 0}")
        print(f"{'='*70}\n")
        
        # Build prompt with strict instructions on using context sections
        system = (
            "You are a personalized university admissions advisor for the Technical University of Munich (TUM).\n\n"
            
            "=== CRITICAL: ONLY USE PROVIDED CONTEXT ===\n"
            "You MUST ONLY answer using information explicitly present in the CONTEXT sections below.\n"
            "DO NOT use any external knowledge, prior training data, or make assumptions.\n"
            "If the answer is not in the context, you MUST say you don't have that information.\n\n"
            
            "=== CONTEXT SECTIONS EXPLAINED ===\n"
            "The CONTEXT below contains up to 3 sections:\n\n"
            
            "1. USER PROFILE: The user's personal information (name, current education, GPA, desired programs, etc.)\n"
            "   → Use this to PERSONALIZE your response and understand the user's background\n\n"
            
            "2. USER DOCUMENTS: Content extracted from the user's uploaded files (CV, transcript, diploma)\n"
            "   → Use this to understand the user's qualifications, skills, and experience\n\n"
            
            "3. TUM KNOWLEDGE BASE: Official TUM program information (requirements, deadlines, processes)\n"
            "   → This is your ONLY source of truth for TUM-specific facts. NEVER invent TUM information.\n\n"
            
            "=== STRICT RULES ===\n"
            "1. ANSWER ONLY FROM CONTEXT - If information is not in the context sections, you MUST NOT answer\n"
            "2. For TUM-specific info (requirements, deadlines, processes): ONLY use TUM KNOWLEDGE BASE section\n"
            "3. For personalizing advice: Use USER PROFILE + USER DOCUMENTS to tailor your response\n"
            "4. If comparing user qualifications to requirements: Cross-reference USER sections with TUM KB\n"
            "5. Keep answers concise (2-4 sentences). Use bullet points for lists\n"
            "6. If TUM KNOWLEDGE BASE is empty or missing, you MUST respond:\n"
            "   'I don't have specific information about that in my knowledge base. Please contact TUM directly at study@tum.de for detailed assistance.'\n"
            "7. If the context doesn't contain enough information to answer fully, say so explicitly\n"
            "8. NEVER make up deadlines, requirements, procedures, or program details not in the context\n"
            "9. When giving personalized advice, explicitly reference the user's data (e.g., 'Based on your GPA of 3.5...')\n"
            "10. If unsure, prefer saying 'I don't have that information' over guessing"
        )
        context = self.compile_context_text(profile, kb_docs, user_docs)
        
        # Check if we have any KB documents or user documents - if not, return "I don't know"
        if not kb_docs and not user_docs:
            print(f"\n{'='*70}")
            print("[AGENT] ✗ No KB documents or user documents available")
            print(f"{'='*70}\n")
            
            answer = "I don't know enough information to answer your question. Please provide more details or contact TUM directly at study@tum.de for detailed assistance."
            
            print(f"\n{'='*70}")
            print("[AGENT] ✓ Answer generated (fallback - no context available):")
            print(f"{'='*70}")
            print(answer)
            print(f"{'='*70}\n")
            
            return answer

        human_prompt = (
            "CONTEXT:\n" + (context or "No context available") + "\n\n" +
            ("CHAT HISTORY:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in (chat_history or [])]) + "\n\n" if chat_history else "") +
            "QUESTION:\n" + question + "\n\n" +
            "Provide a personalized, helpful answer based on the context above."
        )

        try:
            print(f"\n{'='*70}")
            print("[AGENT] Sending prompt to LLM...")
            print(f"{'='*70}\n")
            
            # Use invoke() with SystemMessage and HumanMessage
            resp = self.llm.invoke([
                SystemMessage(content=system),
                HumanMessage(content=human_prompt)
            ], temperature=0)
            
            # Extract textual content safely
            if hasattr(resp, 'content'):
                content = resp.content
                if content is None:
                    return str(resp)
                answer = content.strip()
            else:
                answer = str(resp).strip()
            
            print(f"\n{'='*70}")
            print("[AGENT] ✓ Answer generated:")
            print(f"{'='*70}")
            print(answer)
            print(f"{'='*70}\n")
            
            return answer
        except Exception as e:
            print(f"\n[AGENT] ✗ Error generating answer:")
            traceback.print_exc()
            return f"Error generating answer: {str(e)}"

    # ------------------ Run ------------------
    def run(self, question: str, user_id: Optional[str] = None, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Main entrypoint for agentic question answering."""
        print(f"\n{'='*70}")
        print(f"[AGENT RUN] Starting agentic RAG for question: {question}")
        print(f"  User ID: {user_id or 'None (unauthenticated)'}")
        print(f"{'='*70}\n")
        
        # Step 1: try to fetch a minimal profile summary (non-blocking)
        profile = {}
        if user_id:
            profile = self.fetch_user_profile(user_id)

        # Step 2: plan
        profile_summary = None
        if profile:
            # small summary string
            try:
                profile_summary = profile.get("user", {}).get("first_name") or ""
            except Exception:
                profile_summary = None

        actions = self.plan_actions(question, profile_summary)
        print(f"[AGENT RUN] Planned actions: {actions}")

        # Step 3: perform actions
        kb_docs = []
        user_docs = []

        if "fetch_user_docs" in actions or "search_user_docs" in actions:
            print(f"[AGENT RUN] Fetching user documents...")
            user_docs = self.fetch_user_documents(user_id) if user_id else []
            print(f"[AGENT RUN] Fetched {len(user_docs)} user documents\n")

        if "search_kb" in actions:
            print(f"[AGENT RUN] Searching knowledge base...")
            kb_docs = self.search_kb(question)
            print(f"[AGENT RUN] KB search returned {len(kb_docs)} documents\n")
        else:
            print(f"[AGENT RUN] ⚠ 'search_kb' not in actions - KB will not be consulted!\n")

        if "search_user_docs" in actions and user_docs:
            print(f"[AGENT RUN] Performing vector search on user documents...")
            # refine user doc search
            user_docs = self.search_user_docs(question, user_docs)
            print(f"[AGENT RUN] User doc search returned {len(user_docs)} relevant documents\n")

        # Always include 'answer' as last step
        print(f"[AGENT RUN] Generating final answer with:")
        print(f"  - Profile: {'Yes' if profile else 'No'}")
        print(f"  - KB docs: {len(kb_docs)}")
        print(f"  - User docs: {len(user_docs)}")
        print(f"  - Chat history: {len(chat_history) if chat_history else 0} messages\n")
        
        answer = self.final_answer(question, profile, kb_docs, user_docs, chat_history)
        
        print(f"\n{'='*70}")
        print(f"[AGENT RUN] ✓ Completed")
        print(f"{'='*70}\n")
        
        return answer
