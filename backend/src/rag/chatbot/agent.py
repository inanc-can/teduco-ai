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

import numpy as np
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from db.lib import core as db_core
from core.dependencies import get_signed_url


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
            resp = self.llm.chat([{"role": "user", "content": planner_prompt}], temperature=0)
        except Exception:
            # Fallback: simple heuristic
            if any(word in question.lower() for word in ["my", "me", "i ", "profile", "documents", "transcript"]):
                return ["fetch_profile", "search_user_docs", "search_kb", "answer"]
            return ["search_kb", "answer"]

        # ChatGroq client above might return a string or dict; try to parse JSON
        content = None
        if isinstance(resp, dict):
            # Try to extract typical structure
            content = resp.get("choices", [{}])[0].get("message", {}).get("content") if resp.get("choices") else None
        if content is None:
            try:
                # resp may be a simple string
                content = resp[0]
            except Exception:
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

    def fetch_user_documents(self, user_id: str) -> List[Document]:
        """Download user documents and return as a list of Document objects (page_content and metadata).
        We safely attempt to download text representations. Binary or unparseable files are skipped.
        """
        docs = []
        try:
            result = db_core.get_user_documents(user_id)
            if not result or not getattr(result, "data", None):
                return []

            for entry in result.data:
                storage_path = entry.get("storage_path")
                if not storage_path:
                    continue
                try:
                    url = get_signed_url(storage_path, expires_sec=60)
                    r = self.session.get(url, timeout=10)
                    if r.status_code != 200:
                        continue
                    # Try to decode as text
                    try:
                        text = r.text
                        if len(text.strip()) == 0:
                            continue
                    except Exception:
                        # Can't decode, skip
                        continue

                    metadata = {
                        "source": "user_document",
                        "storage_path": storage_path,
                        "doc_type": entry.get("doc_type"),
                        "document_id": entry.get("document_id"),
                    }
                    docs.append(Document(page_content=text, metadata=metadata))
                except Exception:
                    traceback.print_exc()
                    continue
        except Exception:
            traceback.print_exc()
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
        parts = []
        # Profile summary
        if profile and profile.get("user"):
            user = profile.get("user")
            short = []
            if user.get("first_name") or user.get("last_name"):
                short.append(f"Name: {user.get('first_name','')} {user.get('last_name','')}".strip())
            if profile.get("education"):
                edu = profile.get("education")
                short.append(f"Education: {edu.get('type')} - {edu.get('university_program') or edu.get('high_school_name','')}")
            if profile.get("preferences"):
                prefs = profile.get("preferences")
                if prefs:
                    short.append(f"Preferences: {prefs.get('desired_countries', [])} / {prefs.get('preferred_intake')} ")
            parts.append("USER PROFILE:\n" + " | ".join(short))

        # User documents previews
        if user_docs:
            previews = []
            for d in user_docs[: self.k]:
                preview = d.page_content[:400].replace("\n", " ")
                previews.append(f"- {preview}")
            parts.append("USER DOCUMENTS (top previews):\n" + "\n".join(previews))

        # KB documents
        if kb_docs:
            previews = []
            for d in kb_docs[: self.k]:
                preview_text = d.page_content[:400].replace("\n", " ")
                previews.append(f"- {preview_text}")
            parts.append("KB DOCUMENTS (top previews):\n" + "\n".join(previews))

        return "\n\n".join(parts)

    def final_answer(self, question: str, profile: Dict[str, Any], kb_docs: List[Document], user_docs: List[Document], chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        # Build prompt with strict brevity instruction
        system = (
            "You are a concise university advisor. Use only the provided context sections to answer. "
            "Keep answers extremely short and precise (1-2 sentences). If listing items, use brief bullet points. "
            "If you cannot find the answer in the context, say: 'I don't have that information.'"
        )
        context = self.compile_context_text(profile, kb_docs, user_docs)

        human_prompt = (
            "CONTEXT:\n" + (context or "No context available") + "\n\n" +
            ("CHAT HISTORY:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in (chat_history or [])]) + "\n\n" if chat_history else "") +
            "QUESTION:\n" + question + "\n\n" +
            "Provide a short, precise answer (1-2 sentences)."
        )

        try:
            resp = self.llm.chat([{"role": "system", "content": system}, {"role": "user", "content": human_prompt}], temperature=0)
            # Extract textual content safely
            if isinstance(resp, dict):
                content = resp.get("choices", [{}])[0].get("message", {}).get("content") if resp.get("choices") else None
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
