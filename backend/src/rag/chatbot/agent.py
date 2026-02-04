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
import re
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
from rag.chatbot.db_ops import (
    retrieve_chunks,
    list_all_degree_programs,
    retrieve_user_document_chunks,
    upsert_user_document_chunks,
    upsert_user_profile_chunks,
)

# Try to import PDF parser for document processing
# First try docling (better for scanned PDFs with OCR), then fallback to pymupdf
try:
    from rag.parser.conversion import DoclingPDFParser
    PDF_PARSER_CLASS = DoclingPDFParser
    PDF_PARSER_TYPE = "docling"
    print("[Agent] Using DoclingPDFParser for PDF documents")
except ImportError:
    try:
        from rag.parser.pdf_parser import PDFParser
        PDF_PARSER_CLASS = PDFParser
        PDF_PARSER_TYPE = "pymupdf"
        print("[Agent] DoclingPDFParser not available, using PyMuPDF fallback")
    except ImportError:
        PDF_PARSER_CLASS = None
        PDF_PARSER_TYPE = None
        print("[Agent] Warning: No PDF parser available. PDF documents will be skipped.")


class Agent:
    def __init__(
        self,
        llm: ChatGroq,
        retriever_pipeline,
        embeddings,
        k: int = 15,
        similarity_threshold: float = 0.30,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4
    ):
        self.llm = llm
        self.retriever_pipeline = retriever_pipeline
        self.embeddings = embeddings
        self.k = k
        self.similarity_threshold = similarity_threshold
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight

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
            "The answer step may include asking one or two follow-up questions or suggesting the user upload documents if the question is vague or info is missing.\n"
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
            # Ensure information center is consulted for application/university questions
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
            # Enforce information center for application/university keywords
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

    def _parse_pdf_content(self, pdf_bytes: bytes, filename: str) -> Optional[str]:
        """Parse PDF content to text using available PDF parser.
        
        Uses DoclingPDFParser if available (better OCR support), 
        otherwise falls back to PyMuPDF (faster, text-based PDFs only).
        
        Args:
            pdf_bytes: Raw PDF file content
            filename: Name of the file for logging
            
        Returns:
            Extracted text, or None if parsing fails
        """
        if PDF_PARSER_CLASS is None:
            print(f"[Agent] Skipping PDF {filename}: No PDF parser available")
            return None
        
        try:
            if PDF_PARSER_TYPE == "docling":
                parser = PDF_PARSER_CLASS(force_full_page_ocr=False)
                conversion = parser.convert_document(pdf_bytes, name=filename)
                text = parser.conversion_to_markdown(conversion)
            else:
                # PyMuPDF fallback
                parser = PDF_PARSER_CLASS()
                text = parser.extract_text(pdf_bytes, filename)
            
            if text and len(text.strip()) > 0:
                print(f"[Agent] [OK] Parsed PDF {filename} using {PDF_PARSER_TYPE}: {len(text)} chars")
                return text
        except Exception as e:
            print(f"[Agent] Failed to parse PDF {filename}: {e}")
            traceback.print_exc()
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
                    print(f"[Agent] [OK] Loaded document: {doc_type} ({len(text)} chars)")
                    
                except Exception as e:
                    print(f"[Agent] Error processing document {storage_path}: {e}")
                    traceback.print_exc()
                    continue
                    
        except Exception as e:
            print(f"[Agent] Error fetching user documents: {e}")
            traceback.print_exc()
            
        print(f"[Agent] Total documents loaded: {len(docs)}")
        return docs

    def _expand_query(self, question: str) -> str:
        """Expand query with topic-specific synonyms for better keyword matching."""
        question_lower = question.lower()
        expansions = []

        # Deadline / application timing
        deadline_triggers = [
            "when", "apply", "deadline", "intake", "fall", "winter", "summer",
            "semester", "admission date", "application date", "too late", "time to apply"
        ]
        if any(t in question_lower for t in deadline_triggers):
            expansions.append("application period application deadline when to apply admission deadline")

        # Requirements / eligibility
        req_triggers = [
            "require", "eligib", "qualif", "need", "gpa", "grade", "prerequisite",
            "can i get in", "do i qualify", "enough", "minimum"
        ]
        if any(t in question_lower for t in req_triggers):
            expansions.append("admission requirements entry requirements prerequisites qualification")

        # Language requirements
        lang_triggers = ["language", "english", "german", "ielts", "toefl", "certificate"]
        if any(t in question_lower for t in lang_triggers):
            expansions.append("language proficiency language certificate language requirement")

        # Documents needed / eligibility check (include "list" for "can you give me a list?")
        doc_triggers = ["document", "submit", "upload", "transcript", "diploma", "cv", "motivation", 
                       "what do i need", "do i need", "enough", "ready", "missing", "checklist", 
                       "requirements", "required", "prepare", "list"]
        if any(t in question_lower for t in doc_triggers):
            expansions.append("documents required for online application enrollment higher education entrance qualification proof transcript diploma cv resume passport")

        # Costs / fees
        fee_triggers = ["cost", "fee", "tuition", "price", "pay", "expensive", "afford"]
        if any(t in question_lower for t in fee_triggers):
            expansions.append("tuition fees semester contribution costs")

        if expansions:
            expansion_text = " " + " ".join(expansions)
            print(f"[AGENT KB SEARCH] Query expanded with topic keywords")
            return question + expansion_text

        return question

    def _query_for_retrieval(self, question: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Build a retrieval-effective query for short or follow-up questions using chat context.

        When the user asks something vague like 'can you give me a list?' after discussing a program,
        we need to search for the right program's requirements. This method augments the question
        with program/degree/requirement keywords from recent messages so hybrid search finds the
        correct chunks (e.g. Informatics BSc required documents).
        """
        if not chat_history or len(chat_history) == 0:
            return question

        question_stripped = question.strip()
        question_lower = question_stripped.lower()

        # Follow-up cues: short question or phrases that refer to previous context
        follow_up_cues = [
            "list", "requirements", "what about", "and?", "that", "them", "give me",
            "what are", "which", "how about", "same", "those", "it", "this program"
        ]
        is_short = len(question_stripped) < 50
        is_follow_up = any(c in question_lower for c in follow_up_cues) or is_short

        if not is_follow_up:
            return question

        # Collect text from the last few messages (newest first when iterating backwards)
        recent_texts = []
        for i in range(len(chat_history) - 1, max(-1, len(chat_history) - 5), -1):
            msg = chat_history[i]
            if isinstance(msg, dict) and msg.get("content"):
                recent_texts.append(msg["content"].strip())

        if not recent_texts:
            return question

        # Extract program/degree/requirement keywords from recent context
        combined = " ".join(recent_texts).lower()
        program_terms = []
        if "informatics" in combined:
            program_terms.append("informatics")
        if "mathematics" in combined or "math" in combined:
            program_terms.append("mathematics")
        if "games engineering" in combined or "games" in combined:
            program_terms.append("games engineering")
        if "data science" in combined:
            program_terms.append("data science")
        if "bachelor" in combined or "bsc" in combined or "undergraduate" in combined:
            program_terms.append("bachelor")
        if "master" in combined or "msc" in combined or "mse" in combined or "graduate" in combined:
            program_terms.append("master")
        if any(w in combined for w in ["requirement", "document", "apply", "admission", "list", "need"]):
            program_terms.extend(["requirements", "documents required", "application"])

        if not program_terms:
            return question

        # Build augmented query: original question + context keywords (no duplicate words)
        seen = set(question_lower.split())
        added = []
        for term in program_terms:
            if term not in seen:
                added.append(term)
                seen.add(term)
        if added:
            augmented = question_stripped + " TUM " + " ".join(added)
            print(f"[AGENT RETRIEVAL] Follow-up detected; augmented query for retrieval: {augmented[:120]}...")
            return augmented

        return question

    # Forbidden redirect phrases (only study@tum.de and TUMonline are allowed)
    _REDIRECT_PHRASES = [
        (r"I\s+recommend\s+checking\s+the\s+TUM\s+website[^.]*\.?", "Contact study@tum.de for details."),
        (r"recommend\s+(visiting|checking)\s+(the\s+)?(TUM\s+)?website[^.]*\.?", "Contact study@tum.de for details."),
        (r"check(ing)?\s+the\s+TUM\s+website[^.]*\.?", "Contact study@tum.de for details."),
        (r"visit(ing)?\s+(the\s+)?(TUM\s+)?website[^.]*\.?", "Contact study@tum.de for details."),
        (r"see\s+the\s+TUM\s+website[^.]*\.?", "Contact study@tum.de for details."),
        (r"on\s+the\s+TUM\s+website[^.]*\.?", "Contact study@tum.de for details."),
        (r"the\s+TUM\s+website[^.]*\.?", "Contact study@tum.de for details."),
        (r"(?:visit|check|see)\s+tum\.de[^.]*\.?", "Contact study@tum.de for details."),
        (r"the\s+TUM\s+site[^.]*\.?", "Contact study@tum.de for details."),
        (r"the\s+university\s+website[^.]*\.?", "Contact study@tum.de for details."),
    ]

    def _sanitize_redirects(self, answer: str) -> str:
        """Replace forbidden redirect phrases (TUM website, tum.de) with allowed redirect (study@tum.de only)."""
        if not answer or not answer.strip():
            return answer
        text = answer
        for pattern, replacement in self._REDIRECT_PHRASES:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        # Collapse repeated "Contact study@tum.de for details."
        while "Contact study@tum.de for details. Contact study@tum.de for details." in text:
            text = text.replace(
                "Contact study@tum.de for details. Contact study@tum.de for details.",
                "Contact study@tum.de for details."
            )
        return text

    def _strip_sign_off(self, answer: str) -> str:
        """Remove email-style sign-offs (Best regards, [Your Name], etc.) from the end of the response."""
        if not answer or not answer.strip():
            return answer
        lines = answer.split("\n")
        sign_off_phrases = (
            "best regards", "kind regards", "sincerely", "regards", "cheers",
            "warm regards", "[your name]", "your name"
        )

        def is_sign_off_line(line: str) -> bool:
            low = line.strip().lower()
            if not low:
                return True  # empty line can be part of sign-off block
            return any(p in low or low.startswith(p) for p in sign_off_phrases)

        # From the end, find where the sign-off block starts (first line from bottom that is not sign-off)
        cut = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if not is_sign_off_line(lines[i]):
                cut = i + 1
                break
        return "\n".join(lines[:cut]).strip()

    # ------------------ Search ------------------
    def search_kb(self, question: str, profile: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Search the information center using Supabase hybrid search (semantic + keyword).

        Args:
            question: The user's question
            profile: Optional user profile dict to infer degree level from education type
        """

        # Check if this is a "list all programs" type query
        question_lower = question.lower()
        
        # More flexible detection: if query contains list/show/display + program/degree
        list_trigger = any(kw in question_lower for kw in ["list", "show", "display", "what are", "how many", "total", "count", "tell me about"])
        program_trigger = any(kw in question_lower for kw in ["program", "degree", "course"])
        
        # Also detect "suggest alternatives" or "what else" type queries
        alternative_trigger = any(kw in question_lower for kw in [
            "what else", "other program", "other option", "alternative", "suggest", "recommend",
            "what would you", "which program", "available program", "what program", "different program",
            "instead of", "besides", "apart from"
        ])
        
        # If asking to list/count programs AND not asking specific details
        specific_details = any(kw in question_lower for kw in ["requirement", "deadline", "admission", "language", "when", "how to apply", "credit"])
        
        if (list_trigger and program_trigger and not specific_details) or (alternative_trigger and not specific_details):
            print(f"\n{'='*70}")
            print(f"[AGENT KB SEARCH] Detected 'list all programs' or 'suggest alternatives' query")
            print(f"[AGENT KB SEARCH] Using direct database query instead of vector search")
            print(f"{'='*70}")
            
            programs = list_all_degree_programs()
            
            if not programs:
                print(f"[AGENT KB SEARCH] No programs found in database")
                return []
            
            # Determine which degree level to filter based on user eligibility
            user_applicant_type = None
            if profile:
                user = profile.get("user") or {}
                user_applicant_type = user.get("applicant_type", "") if isinstance(user, dict) else ""
            
            # Filter programs based on user's eligibility
            eligible_level = None
            if user_applicant_type == "high-school":
                eligible_level = "bachelor"
                print(f"[AGENT KB SEARCH] High school student - showing only Bachelor programs")
            elif user_applicant_type == "university":
                eligible_level = "master"
                print(f"[AGENT KB SEARCH] University student - showing only Master programs")
            
            # Create a summary document listing eligible programs
            program_list = []
            for p in programs:
                degree = p.get('degree', 'unknown')
                level = p.get('degree_level', 'unknown')
                source = p.get('source', 'unknown')
                
                # Filter by eligible level if specified
                if eligible_level and level != eligible_level:
                    continue
                    
                program_list.append(f"- {degree.title()} ({level.title()})")
            
            level_text = f" {eligible_level.title()}" if eligible_level else ""
            content = f"TUM{level_text} Degree Programs I can help you with:\n\n" + "\n".join(sorted(set(program_list)))
            content += f"\n\nTotal: {len(set(program_list))} unique{level_text.lower()} degree programs"
            
            if eligible_level == "bachelor" and user_applicant_type == "high-school":
                content += "\n\nNote: As a high school student, you are eligible for Bachelor's programs. Master's programs require a completed Bachelor's degree."
            
            print(f"[AGENT KB SEARCH] Found {len(set(program_list))} eligible programs for user")
            print(f"{'='*70}\n")
            
            return [Document(
                page_content=content,
                metadata={"source": "database_query", "type": "program_list", "count": len(set(program_list)), "degree_level": eligible_level}
            )]
        
        print(f"\n{'='*70}")
        print(f"[AGENT KB SEARCH] Searching information center via Supabase hybrid search...")
        print(f"  Question: {question}")
        print(f"  Semantic weight: {self.semantic_weight}, Keyword weight: {self.keyword_weight}")
        print(f"{'='*70}")
        
        try:
            # 1. Determine degree level filter based on user's eligibility
            # IMPORTANT: High school students can ONLY see Bachelor programs
            # University students can see Master programs
            degree_level_filter = None
            question_lower = question.lower()
            
            # First, check the user's applicant type to determine eligibility
            user_applicant_type = None
            if profile:
                user = profile.get("user") or {}
                user_applicant_type = user.get("applicant_type", "") if isinstance(user, dict) else ""
            
            # High school students: ALWAYS filter to bachelor programs only
            if user_applicant_type == "high-school":
                degree_level_filter = "bachelor"
                if "master" in question_lower or "master's" in question_lower or "msc" in question_lower:
                    print(f"[AGENT KB SEARCH] User is high school student asking about Master's - enforcing Bachelor filter")
                else:
                    print(f"[AGENT KB SEARCH] High school student - filtering to Bachelor programs only")
            # University students: can search for Master's, or Bachelor's if they explicitly ask
            elif user_applicant_type == "university":
                if "bachelor" in question_lower or "bachelor's" in question_lower or "undergraduate" in question_lower or "bsc" in question_lower:
                    degree_level_filter = "bachelor"
                    print(f"[AGENT KB SEARCH] University student asking about Bachelor programs")
                else:
                    degree_level_filter = "master"
                    print(f"[AGENT KB SEARCH] University student - defaulting to Master programs")
            # No profile or unknown type: use question keywords
            else:
                if "bachelor" in question_lower or "bachelor's" in question_lower or "undergraduate" in question_lower or "bsc" in question_lower:
                    degree_level_filter = "bachelor"
                    print(f"[AGENT KB SEARCH] Detected bachelor degree level from question keywords")
                elif "master" in question_lower or "master's" in question_lower or "msc" in question_lower or "mse" in question_lower:
                    degree_level_filter = "master"
                    print(f"[AGENT KB SEARCH] Detected master degree level from question keywords")
            
            # 2. Embed the query (original question for semantic search)
            print(f"[AGENT KB SEARCH] Embedding query...")
            query_embedding = self.embeddings.embed_query(question)

            # 2b. Expand query for keyword search (add synonyms for better matching)
            expanded_query = self._expand_query(question)

            # 3. Retrieve from Supabase using hybrid search
            print(f"[AGENT KB SEARCH] Querying Supabase with k={self.k}...")
            results = retrieve_chunks(
                query=expanded_query,
                query_embedding=query_embedding,
                top_k=self.k * 3,  # Fetch extra to allow threshold filtering
                semantic_weight=self.semantic_weight,
                keyword_weight=self.keyword_weight,
                filter_degree_level=degree_level_filter
            )

            print(f"[AGENT KB SEARCH] Retrieved {len(results)} chunks from Supabase")

            if not results:
                print("[AGENT KB SEARCH] No documents retrieved from Supabase!")
                print(f"{'='*70}\n")
                return []

            # 4. Filter by threshold and take top k
            selected_docs = []
            for idx, res in enumerate(results, 1):
                hybrid_score = res.get("hybrid_score", 0.0)
                similarity = res.get("similarity_score", 0.0)
                keyword_rank = res.get("keyword_rank", 0.0)
                content = res.get("content", "")
                metadata = res.get("metadata") or {}

                if hybrid_score >= self.similarity_threshold:
                    doc = Document(page_content=content, metadata=metadata)
                    doc.metadata['hybrid_score'] = hybrid_score
                    doc.metadata['similarity_score'] = similarity
                    selected_docs.append(doc)
                    source = metadata.get('source', 'unknown')
                    section = metadata.get('section', 'N/A')
                    print(f"[AGENT KB SEARCH]   [{idx}] score={hybrid_score:.4f} sem={similarity:.4f} kw={keyword_rank:.4f} {source} - {section}")

                if len(selected_docs) >= self.k:
                    break

            print(f"[AGENT KB SEARCH] {len(selected_docs)} documents above threshold ({self.similarity_threshold})")

            if not selected_docs:
                print("[AGENT KB SEARCH] No documents above threshold!")
                print(f"{'='*70}\n")
                return []

            print(f"[AGENT KB SEARCH] Returning {len(selected_docs)} documents")
            print(f"{'='*70}\n")
            return selected_docs
            
        except Exception as e:
            print(f"[AGENT KB SEARCH] [FAIL] Exception during search: {e}")
            traceback.print_exc()
            print(f"{'='*70}\n")
            return []
    
    def _mmr_selection(
        self,
        query_embedding: List[float],
        documents: List[Document],
        doc_embeddings: List[List[float]],
        k: int,
        lambda_mult: float = 0.5
    ) -> List[Document]:
        """
        Maximal Marginal Relevance (MMR) selection for diverse document retrieval.
        
        Balances relevance to query with diversity from already-selected documents.
        
        Args:
            query_embedding: Query embedding vector
            documents: Candidate documents
            doc_embeddings: Embeddings for candidate documents (aligned with documents list)
            k: Number of documents to select
            lambda_mult: Tradeoff between relevance (1.0) and diversity (0.0). Default 0.5 is balanced.
        
        Returns:
            List of k selected documents, ordered by MMR score
        """
        if k >= len(documents):
            return documents
        
        # Convert to numpy for efficient computation
        query_emb = np.array(query_embedding)
        doc_embs = np.array(doc_embeddings)
        
        # Normalize embeddings for cosine similarity
        query_emb = query_emb / np.linalg.norm(query_emb)
        doc_embs = doc_embs / np.linalg.norm(doc_embs, axis=1, keepdims=True)
        
        # Calculate query-document similarities (relevance scores)
        query_doc_sims = np.dot(doc_embs, query_emb)
        
        selected_indices = []
        remaining_indices = list(range(len(documents)))
        
        # Select first document (highest relevance)
        first_idx = int(np.argmax(query_doc_sims))
        selected_indices.append(first_idx)
        remaining_indices.remove(first_idx)
        
        # Iteratively select remaining documents
        for _ in range(k - 1):
            if not remaining_indices:
                break
            
            mmr_scores = []
            for idx in remaining_indices:
                # Relevance to query
                relevance = query_doc_sims[idx]
                
                # Max similarity to already-selected documents (redundancy penalty)
                if selected_indices:
                    selected_embs = doc_embs[selected_indices]
                    similarities = np.dot(selected_embs, doc_embs[idx])
                    max_similarity = np.max(similarities)
                else:
                    max_similarity = 0.0
                
                # MMR score: balance relevance and diversity
                mmr_score = lambda_mult * relevance - (1 - lambda_mult) * max_similarity
                mmr_scores.append(mmr_score)
            
            # Select document with highest MMR score
            best_mmr_idx = int(np.argmax(mmr_scores))
            selected_idx = remaining_indices[best_mmr_idx]
            selected_indices.append(selected_idx)
            remaining_indices.remove(selected_idx)
        
        # Return documents in MMR-selected order
        return [documents[i] for i in selected_indices]

    def search_user_docs_supabase(self, question: str, user_id: str) -> List[Document]:
        """Search user documents via Supabase hybrid search (pre-embedded chunks).

        This replaces the old FAISS-based approach. User documents are embedded
        at upload time and stored in rag_user_documents, so search is fast.
        """
        if not user_id:
            return []
        try:
            print(f"[Agent] Searching user documents in Supabase for user {user_id}...")
            query_embedding = self.embeddings.embed_query(question)

            results = retrieve_user_document_chunks(
                user_id=user_id,
                query=question,
                query_embedding=query_embedding,
                top_k=self.k,
                semantic_weight=self.semantic_weight,
                keyword_weight=self.keyword_weight,
            )

            if not results:
                print(f"[Agent] No user document chunks found in Supabase")
                return []

            docs = []
            for r in results:
                hybrid_score = r.get("hybrid_score", 0.0)
                if hybrid_score >= max(self.similarity_threshold - 0.1, 0.1):
                    doc = Document(
                        page_content=r.get("content", ""),
                        metadata=r.get("metadata") or {}
                    )
                    doc.metadata["doc_type"] = r.get("doc_type", "document")
                    doc.metadata["hybrid_score"] = hybrid_score
                    docs.append(doc)
                    print(f"[Agent] User doc score={hybrid_score:.4f} type={r.get('doc_type', 'unknown')}")

            print(f"[Agent] Returning {len(docs)} user document chunks")
            return docs

        except Exception:
            print("[Agent] Error in search_user_docs_supabase:")
            traceback.print_exc()
            return []

    def search_user_docs(self, question: str, user_docs: List[Document]) -> List[Document]:
        """Fallback: build FAISS from in-memory user docs if Supabase search unavailable."""
        if not user_docs:
            return []
        try:
            print(f"[Agent] Building FAISS index for {len(user_docs)} user documents (fallback)...")
            user_vector_store = FAISS.from_documents(
                documents=user_docs,
                embedding=self.embeddings
            )
            results_with_scores = user_vector_store.similarity_search_with_score(
                question, k=self.k
            )
            docs = []
            for doc, score in results_with_scores:
                similarity = 1 / (1 + score)
                if similarity >= max(self.similarity_threshold - 0.1, 0.1):
                    docs.append(doc)
            return docs
        except Exception:
            print("[Agent] Error in search_user_docs fallback:")
            traceback.print_exc()
            return []

    # ------------------ Final Answer ------------------
    def compile_context_text(self, profile: Dict[str, Any], kb_docs: List[Document], user_docs: List[Document]) -> str:
        """
        Compile all retrieved context into a structured text for the LLM.
        
        The context has 3 sections:
        1. USER PROFILE - Personal info from Supabase (name, education, GPA, preferences, current_city)
        2. USER DOCUMENTS - Content from uploaded files (CV, transcript, diploma)
        3. TUM PROGRAM INFORMATION - Retrieved from the information center (Supabase)
        
        The agent should use USER PROFILE + USER DOCUMENTS to understand the user's background,
        and TUM PROGRAM INFORMATION (information center) to provide accurate TUM-specific information.
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
            print("[AGENT CONTEXT] [OK] USER PROFILE available")
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
            print("[AGENT CONTEXT] [FAIL] No USER PROFILE available")

        # ============================================================
        # SECTION 2: USER DOCUMENTS (CV, transcript, diploma from Supabase Storage)
        # This provides detailed background about the user's qualifications
        # ============================================================
        if user_docs:
            print(f"[AGENT CONTEXT] [OK] USER DOCUMENTS available ({len(user_docs)} docs)")
            
            # First, create a summary of uploaded document types for quick reference
            doc_types_uploaded = set()
            doc_parts = []
            for d in user_docs[:self.k]:
                doc_type = d.metadata.get("doc_type", "document")
                doc_types_uploaded.add(doc_type.lower())
                # Keep newlines for better structure
                content = d.page_content[:1500].strip()
                doc_parts.append(f"[{doc_type.upper()}]: {content}")
            
            # Add a summary header showing what documents the user has uploaded
            doc_summary = f"Documents uploaded by user: {', '.join(sorted(doc_types_uploaded))}\n\n"
            parts.append("=== USER DOCUMENTS ===\n" + doc_summary + "\n\n".join(doc_parts))
        else:
            print("[AGENT CONTEXT] [FAIL] No USER DOCUMENTS available")
            # Still add a note that no documents have been uploaded; nudge model to suggest uploads when relevant
            parts.append(
                "=== USER DOCUMENTS ===\n"
                "No documents have been uploaded yet by the user. "
                "If the user asks about their eligibility or required documents, consider suggesting they upload a transcript, diploma, or CV if relevant."
            )

        # ============================================================
        # SECTION 3: TUM PROGRAM INFORMATION (from vector store)
        # This is the ONLY source of truth for TUM-specific information
        # ============================================================
        if kb_docs:
            print(f"[AGENT CONTEXT] [OK] TUM PROGRAM INFO available ({len(kb_docs)} docs)")
            kb_parts = []
            for d in kb_docs[:self.k]:
                source = d.metadata.get("source", "unknown")
                section = d.metadata.get("section", "")
                # Keep newlines for better readability by the LLM
                content = d.page_content[:1500].strip()
                kb_parts.append(f"[Program: {source}] {section}\n{content}")
            parts.append("=== TUM PROGRAM INFORMATION ===\n" + "\n\n".join(kb_parts))
        else:
            print("[AGENT CONTEXT] [FAIL] No TUM PROGRAM INFO retrieved")

        context_text = "\n\n".join(parts) if parts else "No context available"
        
        print(f"\n{'='*70}")
        print("[AGENT CONTEXT DEBUG] Full context compiled:")
        print(f"{'='*70}")
        print(context_text)
        print(f"{'='*70}\n")
        
        return context_text

    # Varied fallback responses when no context is available
    # Use {name} as placeholder to be replaced with actual user name
    _NO_CONTEXT_RESPONSES = [
        "Hey {name}! I don't have specific info on that topic. "
        "I'd recommend reaching out to study@tum.de for the details. Anything else I can help with?",

        "Hmm {name}, that's outside my expertise unfortunately. "
        "For a reliable answer, contact study@tum.de. Is there something else about TUM I can help with?",

        "Good question, {name}! I don't have the details on that one. "
        "The team at study@tum.de can help you out. What else can I assist with?",

        "{name}, I'd rather point you to the right source than guess on this one - try study@tum.de. "
        "In the meantime, anything else I can help you with?",
    ]
    _no_context_idx = 0

    def _get_user_first_name(self, profile: Optional[Dict[str, Any]]) -> str:
        """Extract the user's first name from their profile."""
        if not profile:
            return "there"
        user = profile.get("user") or {}
        full_name = user.get("name", "") if isinstance(user, dict) else ""
        if full_name:
            return full_name.split()[0]  # Get first name
        return "there"

    def final_answer(self, question: str, profile: Dict[str, Any], kb_docs: List[Document], user_docs: List[Document], chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        print(f"\n{'='*70}")
        print("[AGENT] Generating final answer...")
        print(f"  Question: {question}")
        print(f"  Information center docs: {len(kb_docs)}, User docs: {len(user_docs)}")
        print(f"  Chat history length: {len(chat_history) if chat_history else 0}")
        print(f"{'='*70}\n")

        # Build the education consultant system prompt
        system = (
            "You are a friendly but professional education consultant at Teduco, specializing in TUM (Technical University of Munich) admissions. "
            "Be approachable and helpful; keep a professional, precise tone suitable for applicants. Do not use casual slang.\n\n"

            "ABSOLUTE RULE - NEVER VIOLATE:\n"
            "You may ONLY answer based on the information provided in the CONTEXT below (TUM program information from the information center, user profile, and user documents). "
            "If the information is NOT in the context, you DO NOT KNOW IT. "
            "NEVER guess, assume, infer, or fill in gaps with general knowledge. "
            "If you don't have specific information, say: 'I don't have that specific information. Please contact study@tum.de for details.'\n\n"

            "INFORMATION HIERARCHY:\n"
            "1. TUM PROGRAM INFORMATION - Your PRIMARY and ONLY source for TUM-related facts (from the information center)\n"
            "2. USER PROFILE & DOCUMENTS - Use ONLY when the student asks about themselves\n"
            "3. If neither source has the answer → Admit you don't know and redirect to study@tum.de\n\n"

            "WHAT YOU MUST NEVER DO:\n"
            "- NEVER invent deadlines, requirements, GPA thresholds, or any facts\n"
            "- NEVER use general knowledge about TUM or German universities\n"
            "- NEVER assume requirements are 'typical' or 'usually'\n"
            "- NEVER say 'generally', 'typically', 'usually', 'most programs' - only state what's in the context\n"
            "- NEVER fill gaps with educated guesses\n"
            "- NEVER mention 'knowledge base', 'database', 'context', or 'documents' in your responses - speak naturally\n\n"

            "ALLOWED REDIRECTS ONLY - STRICT:\n"
            "You may ONLY direct users to (1) TUMonline (for application/registration/enrollment) and (2) study@tum.de. "
            "NEVER suggest checking or visiting 'the TUM website', 'tum.de', 'the TUM site', 'the university website', "
            "'the official TUM pages', or any similar phrasing. "
            "Do NOT say things like: 'check the TUM website', 'visit tum.de for details', 'see the TUM website', "
            "'I recommend checking the TUM website', 'find more on the TUM site', 'for more information see the TUM website'. "
            "When you don't have information: only say to contact study@tum.de (or to use TUMonline for application steps).\n\n"

            "WHEN TO ASK FOLLOW-UP QUESTIONS:\n"
            "- If the question is ambiguous or you need one or two specific details to give a precise answer (e.g. which program or intake they mean, whether they are an international student, or their current GPA), ask one or two short, specific follow-up questions in the same response. Do not guess.\n"
            "- Once the user provides the details in a later message, use the conversation history and give a complete, straight-to-the-point answer.\n"
            "- Keep follow-up questions brief and concrete (e.g. 'Which program are you applying to: BSc Informatics or MSc?' or 'Are you an international student?').\n\n"

            "WHEN INFORMATION OR DOCUMENTS ARE MISSING:\n"
            "- If the user asks about their eligibility, required documents, or application readiness and relevant profile fields (e.g. applicant type, GPA, university/high school) or uploaded documents (e.g. transcript, diploma, language certificate, CV) are missing: (1) Briefly state what is missing, (2) Suggest they upload the document (via Documents) or complete their profile (e.g. in Settings), (3) Answer as well as you can with the information you have, or say you can give a more precise answer once they upload or complete the profile.\n"
            "- Only suggest uploading or completing what is relevant to the question.\n\n"

            "WHEN YOU ARE UNCERTAIN:\n"
            "- If you are uncertain or the context is ambiguous or incomplete, do not guess. Redirect the user to contact study@tum.de for accurate information.\n\n"

            "WHEN YOU HAVE THE INFORMATION — BE CONFIDENT (CRITICAL):\n"
            "- When the CONTEXT contains the answer (e.g. application deadlines, requirements, process, dates), state it directly and confidently. Do NOT preface with 'you can start by checking TUMonline', 'I recommend contacting study@tum.de', or deflect when the detail is already in the context.\n"
            "- If you retrieved application dates or requirements from the context for the program the user asked about, state them clearly (e.g. 'For Informatics MSc, the application period for the winter semester is 1 February to 31 May and for the summer semester 1 October to 30 November.'). Do NOT then say 'I don't have specific information' for that same program.\n"
            "- Only suggest contacting study@tum.de or TUMonline when the specific information is genuinely NOT in the context. When you have the information, give it as a fact — do not hedge or redirect.\n"
            "- Never mix: do not give dates for one program and then say you lack information for the program they asked about. Either state what the context says for their program or say you don't have that program and redirect.\n\n"

            "YOUR COMMUNICATION STYLE:\n"
            "- BE CONCISE: 3-5 sentences for simple questions, bullet points for lists\n"
            "- BE DIRECT: Answer first, add context if needed. When the context has the answer, state it as a fact — do not hedge or suggest they contact someone for that same information\n"
            "- USE THEIR NAME: Address them by first name naturally\n"
            "- BE HONEST: If you don't have info, say so immediately - don't hedge or guess\n"
            "- BE CONFIDENT: When you have retrieved the answer from the context, state it clearly. Do not say 'I recommend' or 'I don't have specific information' when you have just stated or could state that information from the context\n"
            "- SPEAK NATURALLY: Never reference where your information comes from - just state facts confidently\n"
            "- After you have enough information (from context or the user's answers to your follow-up questions), give a complete answer that is straight to the point: no unnecessary padding; use bullets for lists\n\n"

            "WHEN TO USE USER DATA:\n"
            "- Only reference USER PROFILE/DOCUMENTS when the student asks about their own situation\n"
            "- For comparing their qualifications to requirements\n"
            "- For checking what documents they've uploaded\n"
            "- NEVER use user data to fill in gaps about TUM programs\n\n"

            "DEGREE AND INTERNATIONAL STUDENT RULES:\n"
            "- High school students → Bachelor's only; university students/graduates → Master's programs\n"
            "- If from the USER PROFILE or RECENT CONVERSATION the student appears to be an international applicant (e.g. they said they are from abroad, non-German qualification, or current_city/country suggests it), emphasize requirements from the context that apply to international applicants (e.g. VPD, language certificates, country-specific documents) when relevant. Only state what appears in the context.\n"
            "- If they appear to be a domestic/German applicant, emphasize requirements that apply to domestic qualifications when relevant. Only state what appears in the context.\n"
            "- If unclear, you may ask a short follow-up (e.g. 'Are you applying with a qualification from outside Germany?') to tailor advice.\n\n"

            "CRITICAL RULES:\n\n"

            "1. PROGRAMS - Only discuss programs explicitly in the context:\n"
            "   - If a program isn't in the context, say: 'I don't have information on that program. Contact study@tum.de.'\n\n"

            "2. DOCUMENT CHECKS:\n"
            "   - Only list requirements that appear in the context\n"
            "   - Use ✅/❌ to show what they have vs. need\n\n"

            "3. WHEN YOU DON'T KNOW (TUM facts not in context):\n"
            "   - Say directly: 'I don't have that specific information.'\n"
            "   - Always redirect: 'Please contact study@tum.de for details.'\n"
            "   - When you DO have the information in the context (e.g. dates, requirements), state it confidently; only redirect when the information is truly not in the context.\n"
            "   - Don't apologize excessively, just be direct and helpful\n\n"

            "RESPONSE FORMAT:\n"
            "- Simple questions → 2-4 sentences\n"
            "- Lists → Bullet points only\n"
            "- Missing info → State what you don't know + redirect to study@tum.de\n"
            "- Do NOT use sign-offs. Never end with 'Best regards', 'Sincerely', 'Kind regards', '[Your Name]', or any similar closing. End with the answer only.\n"
        )

        context = self.compile_context_text(profile, kb_docs, user_docs)

        # No information center docs - check if user is asking for program suggestions
        # If so, fetch and list available programs (filtered by eligibility)
        if not kb_docs and not user_docs:
            question_lower = question.lower()
            # Check if this is a "suggest programs" or "what else" type query
            suggest_trigger = any(kw in question_lower for kw in [
                "what else", "other program", "alternative", "suggest", "recommend",
                "what would you", "which program", "available", "what program", 
                "instead", "besides", "apart from", "options"
            ])
            
            if suggest_trigger:
                print(f"[AGENT] No information center results but user asking for suggestions - fetching eligible programs")
                programs = list_all_degree_programs()
                
                if programs:
                    # Determine eligibility based on user profile
                    user_applicant_type = None
                    if profile:
                        user = profile.get("user") or {}
                        user_applicant_type = user.get("applicant_type", "") if isinstance(user, dict) else ""
                    
                    eligible_level = None
                    if user_applicant_type == "high-school":
                        eligible_level = "bachelor"
                    elif user_applicant_type == "university":
                        eligible_level = "master"
                    
                    # Create a list of unique programs filtered by eligibility
                    program_set = set()
                    for p in programs:
                        degree = p.get('degree', 'unknown')
                        level = p.get('degree_level', 'unknown')
                        
                        # Filter by eligible level if specified
                        if eligible_level and level != eligible_level:
                            continue
                            
                        program_set.add(f"{degree.title()} ({level.title()})")
                    
                    program_list_text = "\n".join(f"- {p}" for p in sorted(program_set))
                    
                    level_text = f" {eligible_level.title()}" if eligible_level else ""
                    content = f"TUM{level_text} Degree Programs I can help you with:\n\n{program_list_text}\n\nTotal: {len(program_set)} unique programs"
                    
                    if eligible_level == "bachelor" and user_applicant_type == "high-school":
                        content += "\n\nNote: As a high school student, you are eligible for Bachelor's programs. Master's programs require a completed Bachelor's degree."
                    
                    # Create a synthetic information-center doc with program list
                    kb_docs = [Document(
                        page_content=content,
                        metadata={"source": "database_query", "type": "program_list", "count": len(program_set), "degree_level": eligible_level}
                    )]
                    context = self.compile_context_text(profile, kb_docs, user_docs)
                    print(f"[AGENT] Added {len(program_set)} eligible programs to context")
            
            # Only use fallback if no context at all (no profile, no kb docs, no user docs)
            # If profile is available, the LLM can still answer personal questions
            has_profile = profile and profile.get("user")
            if not kb_docs and not user_docs and not has_profile:
                Agent._no_context_idx = (Agent._no_context_idx + 1) % len(Agent._NO_CONTEXT_RESPONSES)
                first_name = self._get_user_first_name(profile)
                answer = Agent._NO_CONTEXT_RESPONSES[Agent._no_context_idx].format(name=first_name)
                print(f"[AGENT] No context available (no profile, no information center, no user docs), using fallback")
                return answer

        human_prompt = "CONTEXT:\n" + (context or "No context available") + "\n\n"
        if chat_history:
            # Use last 24 messages (12 turns) so follow-up answers have full conversation context
            human_prompt += "RECENT CONVERSATION:\n" + "\n".join(
                [f"{m['role'].upper()}: {m['content']}" for m in (chat_history or [])[-24:]]
            ) + "\n\n"
        human_prompt += (
            "STUDENT'S QUESTION:\n" + question + "\n\n"
            "CRITICAL REMINDERS:\n"
            "- ONLY use information from the CONTEXT above - NEVER make up facts\n"
            "- When the CONTEXT contains the answer (e.g. application dates, deadlines, requirements), state it clearly and confidently. Do NOT say 'I recommend contacting study@tum.de' or 'you can start by checking TUMonline' for that same information — give the answer from the context.\n"
            "- If the answer is NOT in the context, say: 'I don't have that information. Contact study@tum.de.'\n"
            "- NEVER guess, assume, or use general knowledge about TUM\n"
            "- NEVER mention 'information center', 'context', 'database', or 'documents' in your reply - speak naturally\n"
            "- REDIRECTS: Only allow study@tum.de or TUMonline. NEVER suggest 'the TUM website', 'tum.de', or 'check the TUM website'.\n"
            "- Do NOT use sign-offs (Best regards, Sincerely, [Your Name], etc.). End with the answer only.\n"
            "- Use their first name naturally\n"
            "- Be concise, direct, and confident when you have the information"
        )

        try:
            resp = self.llm.invoke([
                SystemMessage(content=system),
                HumanMessage(content=human_prompt)
            ], temperature=0)

            if hasattr(resp, 'content'):
                content = resp.content
                if content is None:
                    return str(resp)
                answer = content.strip()
            else:
                answer = str(resp).strip()

            print(f"[AGENT] Answer generated ({len(answer)} chars)")
            answer = self._sanitize_redirects(answer)
            answer = self._strip_sign_off(answer)
            return answer
        except Exception as e:
            print(f"[AGENT] Error generating answer: {e}")
            traceback.print_exc()
            return f"Error generating answer: {str(e)}"

    # ------------------ Input Guard ------------------
    JAILBREAK_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above|prior|earlier)\s+(instructions|prompts|rules|context)",
        r"forget\s+(everything|all|your|the)\s*(instructions|rules|prompts|context)?",
        r"disregard\s+(all\s+)?(previous|above|prior|your)\s*(instructions|prompts|rules)",
        r"you\s+are\s+now\s+(?!a\s+(tum|university|admissions))",
        r"pretend\s+(you\s+are|to\s+be|you're)",
        r"act\s+as\s+(if\s+you\s+are|a\s+(?!university|admissions|tum))",
        r"from\s+now\s+on[,]?\s+you",
        r"new\s+instructions?\s*:",
        r"\[system\s*(update|message|prompt|override)\]",
        r"override\s+(your|the|all)\s*(system|instructions|rules|prompt)",
        r"repeat\s+(your|the|all)\s*(system\s*)?(instructions|prompt|rules)",
        r"output\s+(your|the)\s*(system\s*)?(prompt|instructions|rules)",
        r"reveal\s+(your|the)\s*(system\s*)?(prompt|instructions|rules)",
        r"what\s+(are|is)\s+your\s+(system\s*)?(prompt|instructions|rules)",
        r"do\s+not\s+use\s+(the\s+)?(context|knowledge\s*base)",
        r"stop\s+being\s+(a\s+)?(university|admissions|tum)",
    ]

    REJECTION_MESSAGE = (
        "I'm sorry, but your message appears to contain instructions that attempt to alter my behavior. "
        "I am a TUM admissions advisor and can only help with questions about TUM degree programs, "
        "admissions requirements, and application processes. Please rephrase your question."
    )

    def _detect_prompt_injection(self, text: str) -> bool:
        """Check if the input text contains prompt injection patterns.

        Returns True if a jailbreak attempt is detected, False otherwise.
        """
        text_lower = text.lower()
        for pattern in self.JAILBREAK_PATTERNS:
            if re.search(pattern, text_lower):
                print(f"[AGENT GUARD] [WARN] Prompt injection detected! Pattern matched: {pattern}")
                return True
        return False

    # ------------------ Run ------------------
    def run(self, question: str, user_id: Optional[str] = None, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Main entrypoint for agentic question answering."""
        print(f"\n{'='*70}")
        print(f"[AGENT RUN] Starting agentic RAG for question: {question}")
        print(f"  User ID: {user_id or 'None (unauthenticated)'}")
        print(f"{'='*70}\n")

        # Step 0: Input guard
        if self._detect_prompt_injection(question):
            print(f"[AGENT RUN] Blocked: prompt injection detected")
            return self.REJECTION_MESSAGE

        # Step 1: Always fetch profile for authenticated users
        profile = {}
        if user_id:
            profile = self.fetch_user_profile(user_id)

        # Step 2: Build a richer profile summary for the planner
        profile_summary = None
        if profile and profile.get("user"):
            user = profile.get("user", {})
            edu = profile.get("education", {})
            prefs = profile.get("preferences", {})
            parts = []
            if user.get("first_name"):
                parts.append(f"Name: {user.get('first_name')} {user.get('last_name', '')}")
            if user.get("applicant_type"):
                parts.append(f"Type: {user.get('applicant_type')}")
            if edu:
                if edu.get("type") == "university":
                    parts.append(f"Studies: {edu.get('university_program', '')} at {edu.get('university_name', '')}")
                    if edu.get("gpa"):
                        parts.append(f"GPA: {edu.get('gpa')}")
                    if edu.get("research_focus"):
                        parts.append(f"Research: {edu.get('research_focus')}")
                elif edu.get("type") == "high-school":
                    parts.append(f"School: {edu.get('high_school_name', '')}")
                    if edu.get("gpa"):
                        parts.append(f"GPA: {edu.get('gpa')}/{edu.get('gpa_scale', '')}")
            if prefs.get("desired_fields"):
                parts.append(f"Fields: {', '.join(prefs.get('desired_fields', []))}")
            profile_summary = "; ".join(parts) if parts else None

        actions = self.plan_actions(question, profile_summary)
        print(f"[AGENT RUN] Planned actions: {actions}")

        # Use chat history to build a retrieval-effective query for follow-ups (e.g. "can you give me a list?")
        retrieval_question = self._query_for_retrieval(question, chat_history)

        # Step 3: Always search information center for authenticated education queries
        kb_docs = []
        user_docs = []

        # Always search information center (the core value of this chatbot)
        if "search_kb" in actions or user_id:
            print(f"[AGENT RUN] Searching information center...")
            kb_docs = self.search_kb(retrieval_question, profile=profile)
            print(f"[AGENT RUN] Information center search returned {len(kb_docs)} documents\n")

        # Always search user docs for authenticated users (core value of personalization)
        if user_id:
            print(f"[AGENT RUN] Searching user documents in Supabase...")
            user_docs = self.search_user_docs_supabase(retrieval_question, user_id)
            if not user_docs:
                # Fallback: fetch and search in memory
                print(f"[AGENT RUN] No Supabase user docs, trying in-memory fallback...")
                raw_docs = self.fetch_user_documents(user_id)
                if raw_docs:
                    user_docs = self.search_user_docs(retrieval_question, raw_docs)
            print(f"[AGENT RUN] User doc search returned {len(user_docs)} documents\n")

        print(f"[AGENT RUN] Generating final answer with:")
        print(f"  - Profile: {'Yes' if profile.get('user') else 'No'}")
        print(f"  - Information center docs: {len(kb_docs)}")
        print(f"  - User docs: {len(user_docs)}")
        print(f"  - Chat history: {len(chat_history) if chat_history else 0} messages\n")

        answer = self.final_answer(question, profile, kb_docs, user_docs, chat_history)

        print(f"\n{'='*70}")
        print(f"[AGENT RUN] Completed")
        print(f"{'='*70}\n")

        return answer
