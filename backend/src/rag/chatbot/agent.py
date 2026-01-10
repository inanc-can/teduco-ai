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
        similarity_threshold: float = 0.55,
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
            return [a.strip().lower() for a in actions]
        except Exception:
            # Best-effort parse: look for keywords
            lc = content.lower() if isinstance(content, str) else ""
            actions = []
            for a in ["fetch_profile", "fetch_user_docs", "search_user_docs", "search_kb", "answer"]:
                if a in lc:
                    actions.append(a)
            if not actions:
                return ["search_kb", "answer"]
            return actions

    # ------------------ Fetching ------------------
    def fetch_user_profile(self, user_id: str) -> Dict[str, Any]:
        try:
            profile = db_core.get_user_profile(user_id)
            return profile
        except Exception:
            traceback.print_exc()
            return {}

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
        try:
            vs = self.retriever_pipeline.vector_store
            if vs is None:
                return []
            results = vs.similarity_search_with_score(question, k=self.k)
            # results are tuples (Document, score) where lower score = closer (L2)
            docs = [doc for doc, score in results if (1 / (1 + score)) >= self.similarity_threshold]
            return docs
        except Exception:
            traceback.print_exc()
            return []

    def search_user_docs(self, question: str, user_docs: List[Document]) -> List[Document]:
        """Embed the user docs and the query and return the top-k relevant user docs."""
        if not user_docs:
            return []
        try:
            texts = [d.page_content for d in user_docs]
            doc_embed = self.embeddings.embed_documents(texts)
            q_embed = self.embeddings.embed_query(question)

            # Compute cosine similarities
            docs_arr = np.array(doc_embed)
            q_arr = np.array(q_embed)
            norms = (np.linalg.norm(docs_arr, axis=1) * np.linalg.norm(q_arr)) + 1e-8
            sims = (docs_arr @ q_arr) / norms
            # Get top k
            top_idx = np.argsort(-sims)[: self.k]
            results = []
            for idx in top_idx:
                if sims[idx] >= self.similarity_threshold:
                    results.append(user_docs[int(idx)])
            return results
        except Exception:
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
        parts = []
        
        # ============================================================
        # SECTION 1: USER PROFILE (from Supabase database tables)
        # This helps the agent understand WHO the user is
        # ============================================================
        if profile and profile.get("user"):
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

        # ============================================================
        # SECTION 2: USER DOCUMENTS (CV, transcript, diploma from Supabase Storage)
        # This provides detailed background about the user's qualifications
        # ============================================================
        if user_docs:
            doc_parts = []
            for d in user_docs[:self.k]:
                doc_type = d.metadata.get("doc_type", "document")
                # Include more content (up to 1500 chars) for better context
                content = d.page_content[:1500].replace("\n", " ").strip()
                doc_parts.append(f"[{doc_type.upper()}]: {content}")
            parts.append("=== USER DOCUMENTS ===\n" + "\n\n".join(doc_parts))

        # ============================================================
        # SECTION 3: KB DOCUMENTS (TUM program info from FAISS vector store)
        # This is the ONLY source of truth for TUM-specific information
        # ============================================================
        if kb_docs:
            kb_parts = []
            for d in kb_docs[:self.k]:
                source = d.metadata.get("source", "unknown")
                section = d.metadata.get("section", "")
                # Include more content for accurate answers
                content = d.page_content[:1500].replace("\n", " ").strip()
                kb_parts.append(f"[Source: {source}] {section}\n{content}")
            parts.append("=== TUM KNOWLEDGE BASE ===\n" + "\n\n".join(kb_parts))

        return "\n\n".join(parts) if parts else "No context available"

    def final_answer(self, question: str, profile: Dict[str, Any], kb_docs: List[Document], user_docs: List[Document], chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        # Build prompt with strict instructions on using context sections
        system = (
            "You are a personalized university admissions advisor for the Technical University of Munich (TUM).\n\n"
            
            "=== CONTEXT SECTIONS EXPLAINED ===\n"
            "The CONTEXT below contains up to 3 sections:\n\n"
            
            "1. USER PROFILE: The user's personal information (name, current education, GPA, desired programs, etc.)\n"
            "   → Use this to PERSONALIZE your response and understand the user's background\n\n"
            
            "2. USER DOCUMENTS: Content extracted from the user's uploaded files (CV, transcript, diploma)\n"
            "   → Use this to understand the user's qualifications, skills, and experience\n\n"
            
            "3. TUM KNOWLEDGE BASE: Official TUM program information (requirements, deadlines, processes)\n"
            "   → This is your ONLY source of truth for TUM-specific facts. NEVER invent TUM information.\n\n"
            
            "=== STRICT RULES ===\n"
            "1. For TUM-specific info (requirements, deadlines, processes): ONLY use TUM KNOWLEDGE BASE section\n"
            "2. For personalizing advice: Use USER PROFILE + USER DOCUMENTS to tailor your response\n"
            "3. If comparing user qualifications to requirements: Cross-reference USER sections with TUM KB\n"
            "4. Keep answers concise (2-4 sentences). Use bullet points for lists\n"
            "5. If TUM KNOWLEDGE BASE is missing or doesn't contain the answer, respond with:\n"
            "   'I don't have specific information about that in my knowledge base. "
            "Please contact TUM directly at study@tum.de for more detailed assistance.'\n"
            "6. NEVER invent deadlines, requirements, or procedures not explicitly in the context\n"
            "7. When giving personalized advice, explicitly reference the user's data (e.g., 'Based on your GPA of 3.5...')"
        )
        context = self.compile_context_text(profile, kb_docs, user_docs)

        human_prompt = (
            "CONTEXT:\n" + (context or "No context available") + "\n\n" +
            ("CHAT HISTORY:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in (chat_history or [])]) + "\n\n" if chat_history else "") +
            "QUESTION:\n" + question + "\n\n" +
            "Provide a personalized, helpful answer based on the context above."
        )

        try:
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
                return content.strip()
            return str(resp).strip()
        except Exception as e:
            traceback.print_exc()
            return f"Error generating answer: {str(e)}"

    # ------------------ Run ------------------
    def run(self, question: str, user_id: Optional[str] = None, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Main entrypoint for agentic question answering."""
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

        # Step 3: perform actions
        kb_docs = []
        user_docs = []

        if "fetch_user_docs" in actions or "search_user_docs" in actions:
            user_docs = self.fetch_user_documents(user_id) if user_id else []

        if "search_kb" in actions:
            kb_docs = self.search_kb(question)

        if "search_user_docs" in actions and user_docs:
            # refine user doc search
            user_docs = self.search_user_docs(question, user_docs)

        # Always include 'answer' as last step
        answer = self.final_answer(question, profile, kb_docs, user_docs, chat_history)
        return answer
