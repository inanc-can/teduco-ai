# RAG Pipeline — Technical Reference

**Product presentation & developer reference.**  
Complete technical documentation of the RAG pipeline: models, retrieval, chunking, tech stack, and configuration.

---

## 1. Tech stack overview

| Layer | Technology | Purpose |
|-------|------------|--------|
| **LLM** | Groq (ChatGroq) | Answer generation; fast inference. |
| **Embeddings** | HuggingFace / sentence-transformers | Dense vector embeddings for semantic search. |
| **Vector storage** | Supabase (pgvector) | Store and query embeddings; hybrid search in SQL. |
| **Chunking** | LangChain text splitters | Split documents into fixed-size or header-based chunks. |
| **Orchestration** | LangChain | Pipeline, prompts, document handling. |
| **PDF parsing** | PyMuPDF (default), Docling (optional) | Extract text from PDFs for ingestion and user docs. |
| **Local vector store (optional)** | FAISS | In-memory fallback for user docs when Supabase search has no results. |
| **Backend** | FastAPI, Supabase client | API, auth, DB and RPC calls. |

---

## 2. Models and configuration

### 2.1 LLM (answer generation)

| Parameter | Value | Notes |
|-----------|--------|-------|
| **Provider** | Groq | |
| **Model** | `meta-llama/llama-4-scout-17b-16e-instruct` | Configured in `rag/chatbot/config.py` as `GROQ_MODEL`. |
| **Temperature** | `0` | Deterministic, fact-focused answers. |
| **Max tokens** | `1000` | Keeps responses concise. |
| **API** | `GROQ_API_KEY` (env) | Required for pipeline startup. |

Model choice is centralized in `backend/src/rag/chatbot/config.py`; the pipeline and Agent use it at runtime.

### 2.2 Embeddings (semantic search)

| Parameter | Value | Notes |
|-----------|--------|-------|
| **Model** | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Multilingual; same for university docs and user docs. |
| **Vector dimension** | **384** | Must match Supabase `vector(384)` in RAG tables. |
| **Normalization** | `normalize_embeddings: True` | Required for correct cosine similarity. |
| **Device** | `cpu` | No GPU dependency. |
| **Cache** | `/app/.hf_cache` (Docker) or default | Model cache directory. |

Used for:

- University degree chunks → `rag_uni_degree_documents`
- User document chunks → `rag_user_documents`
- User profile summary → `rag_user_profile_chunks`
- Query embedding at request time

---

## 3. Retrieval

### 3.1 Strategy: hybrid search

Retrieval combines **semantic similarity** and **keyword relevance**:

- **Semantic**: Cosine similarity between query embedding and chunk embedding (`1 - (embedding <=> query_embedding)` in pgvector).
- **Keyword**: PostgreSQL full-text search — `to_tsvector('english', content)` and `plainto_tsquery('english', query_text)` with `ts_rank_cd(..., 32)`.

Keyword scores are **normalized to [0, 1]** within the result set (divide by max rank) so they can be combined with semantic scores.

**Hybrid score formula:**

```text
hybrid_score = semantic_weight * similarity + keyword_weight * keyword_norm_rank
```

Default weights: **semantic 0.6**, **keyword 0.4** (slightly favor meaning over exact terms).

### 3.2 Top-k and threshold

| Parameter | Value | Where used |
|-----------|--------|------------|
| **k (top_k)** | **15** | Number of chunks to use for the LLM context (KB retrieval). |
| **Fetch size (KB)** | `k * 3` (e.g. 45) | Agent fetches more from DB, then filters by threshold and keeps top k. |
| **Similarity threshold** | **0.30** | Minimum `hybrid_score` to keep a chunk (KB). |
| **User-doc threshold** | `max(0.1, similarity_threshold - 0.1)` | Slightly more permissive for user documents. |

Chunks below threshold are discarded; remaining are ordered by `hybrid_score` and trimmed to top k.

### 3.3 Where retrieval runs

- **University degree docs**: Supabase RPC `hybrid_search_uni_degree_documents` (table `rag_uni_degree_documents`). Optional filters: `filter_degree_level`, `filter_university`, `filter_degree`.
- **User documents**: Supabase RPC `hybrid_search_user_documents` (table `rag_user_documents`), scoped by `user_id`.
- **Fallback**: If no user-doc results from Supabase, Agent can fetch raw user files from Storage, parse PDFs, build an in-memory **FAISS** index, and run `similarity_search_with_score(question, k=self.k)`.

### 3.4 Query expansion and follow-ups

- **Query expansion** (KB only): Before keyword search, the query can be expanded with synonyms (e.g. “deadline” → add “application period”, “when to apply”) to improve keyword recall.
- **Follow-up context**: For short or follow-up questions, the Agent can augment the retrieval query with program/degree/requirement keywords taken from the last few chat messages so the right program is searched.

---

## 4. Chunking

### 4.1 University degree documents (ingestion)

| Parameter | Value | Notes |
|-----------|--------|-------|
| **Chunk size** | **500** (characters) | |
| **Chunk overlap** | **50** (characters) | |
| **Splitters** | `RecursiveTextSplitter` (recursive character); `MarkdownHeaderSplitter` (## headers) | Loader uses both depending on source. |
| **Long-doc rule** | Only split if length > `chunk_size * 2` (1000+ chars) | Shorter metadata docs kept as one chunk. |

Source: `DocumentLoader` + `loaded_docs_to_chunks()` in `loader.py`; ingestion uses same chunk_size/overlap (e.g. in `rag_data_ingestions`).

### 4.2 User-uploaded documents

| Parameter | Value | Notes |
|-----------|--------|-------|
| **Chunk size** | **500** | |
| **Chunk overlap** | **50** | |
| **Splitter** | `RecursiveCharacterTextSplitter` | In documents router background task. |

After upload, text is extracted (PDF or plain text), split, embedded with the same embedding model, and upserted into `rag_user_documents` (per user, per doc_type; re-upload replaces chunks for that doc_type).

### 4.3 User profile (for RAG)

Profile is turned into a single text summary (no chunking). That summary is embedded once and stored in `rag_user_profile_chunks`. The Agent usually reads profile from DB (users + education + preferences) directly; profile chunks can support future profile-aware retrieval.

---

## 5. Step-by-step: how the RAG pipeline runs

This section walks through the pipeline from the user’s question to the final answer. Each step is executed in order.

| Step | What happens | Outcome |
|------|----------------|--------|
| **1. Input** | The system receives the user’s **question**, optional **user_id** (if logged in), and **chat_history** (recent messages in the conversation). | Ready to run the pipeline. |
| **2. Input guard** | The question is checked for **prompt-injection** patterns (e.g. “ignore previous instructions”, “you are now …”). | If detected → return a fixed rejection message and stop. Otherwise continue. |
| **3. Fetch profile** | If `user_id` is present, the system loads the user’s **profile** from the database (name, applicant type, education, preferences). | Profile available for planning and context (or empty if not logged in). |
| **4. Plan actions** | A **planner** (LLM or heuristic) decides which actions to take: e.g. `fetch_profile`, `fetch_user_docs`, `search_kb`, `search_user_docs`, `answer`. | Ordered list of actions (e.g. search KB + search user docs + answer). |
| **5. Build retrieval query** | For short or follow-up questions (e.g. “can you give me a list?”), the **retrieval query** is enriched with keywords from recent chat (e.g. program name, “requirements”). | A single query string used for both KB and user-doc search. |
| **6. Search knowledge base (KB)** | The query is **embedded** with the same model used for ingestion. Optionally the query is **expanded** with synonyms (deadlines, requirements, etc.). The system calls **hybrid search** on the university degree table with optional **degree_level** filter (bachelor/master from profile or question). Results are filtered by **hybrid_score ≥ 0.30** and the **top k** chunks are kept. | List of **kb_docs** (TUM program chunks). |
| **7. Search user documents** | If the user is logged in, the same query (and its embedding) is used to run **hybrid search** on the user’s document chunks in the DB. If that returns nothing, the system may **fetch** the user’s raw files from storage, **parse** PDFs, build an in-memory **FAISS** index, and run similarity search. | List of **user_docs** (chunks from transcript, CV, diploma, etc.). |
| **8. Compile context** | All gathered information is merged into one **context** string with three sections: **USER PROFILE** (from DB), **USER DOCUMENTS** (retrieved chunks, with doc type labels), **TUM PROGRAM INFORMATION** (retrieved KB chunks). Each chunk is truncated (e.g. 1500 chars) to control prompt size. | Single **context** string passed to the LLM. |
| **9. Call LLM** | The **system prompt** (see Section 6) and the **human message** (context + recent conversation + student’s question + short reminders) are sent to the **Groq LLM**. Temperature is 0. | Raw **answer** text. |
| **10. Post-process** | The answer is **sanitized**: forbidden phrases (e.g. “check the TUM website”, “visit tum.de”) are replaced with the allowed redirect (study@tum.de). **Sign-offs** (e.g. “Best regards”, “[Your Name]”) are stripped from the end. | **Final answer** returned to the user. |

**Special cases:**

- **“List all programs” / “suggest programs”**: If the KB search is not used for a specific fact, the system may call `list_unique_degree_programs` and build a single “program list” document, filtered by the user’s eligibility (high school → bachelor, university → master), and use that as TUM PROGRAM INFORMATION.
- **No context at all**: If there is no profile, no KB docs, and no user docs, and the user is not asking for program suggestions, the system returns one of several fixed fallback messages (e.g. “I don’t have specific info … contact study@tum.de”).

---

## 6. System prompt: what it is and how it improves results

The **system prompt** is the fixed instruction set sent to the LLM on every request. It defines the assistant’s role, what it may and may not do, and how it should respond. The actual text lives in `backend/src/rag/chatbot/agent.py` in `Agent.final_answer()` (variable `system`). Below is a structured summary and how each part improves results.

### 6.1 Structure of the system prompt

| Block | Purpose |
|-------|--------|
| **Role** | “Education consultant at Teduco, specializing in TUM admissions”; friendly, professional, no casual slang. |
| **ABSOLUTE RULE** | Answer **only** from the CONTEXT (TUM program info, user profile, user documents). If something is not in the context, do not claim to know it; say “I don’t have that specific information. Please contact study@tum.de for details.” |
| **INFORMATION HIERARCHY** | (1) TUM PROGRAM INFORMATION = primary source for TUM facts; (2) USER PROFILE & DOCUMENTS = only when the student asks about themselves; (3) If neither has the answer → admit and redirect to study@tum.de. |
| **WHAT YOU MUST NEVER DO** | Never invent deadlines/requirements/GPA; never use general knowledge about TUM or German universities; never say “typically”/“usually”; never mention “knowledge base”, “context”, “database”, “documents” in the reply. |
| **ALLOWED REDIRECTS ONLY** | May only direct to **TUMonline** (application/registration) and **study@tum.de**. Never suggest “the TUM website”, “tum.de”, “check the TUM website”, etc. |
| **WHEN TO ASK FOLLOW-UP QUESTIONS** | If the question is ambiguous or one or two details are needed (e.g. which program, intake, international or not), ask one or two short follow-up questions; then use conversation history to give a complete answer. |
| **WHEN INFORMATION OR DOCUMENTS ARE MISSING** | If the user asks about eligibility/documents and profile or uploads are missing: state what’s missing, suggest completing profile or uploading documents, then answer as well as possible or say you can be more precise once they do. |
| **WHEN YOU ARE UNCERTAIN** | Do not guess; redirect to study@tum.de. |
| **WHEN YOU HAVE THE INFORMATION — BE CONFIDENT** | If the context contains the answer (e.g. dates, requirements), state it directly. Do not preface with “check TUMonline” or “contact study@tum.de” for that same information. Only redirect when the information is genuinely not in the context. |
| **COMMUNICATION STYLE** | Concise (3–5 sentences, bullets for lists); direct (answer first); use first name; honest when info is missing; confident when info is present; never reveal “context” or “documents”; no padding. |
| **WHEN TO USE USER DATA** | Only when the student asks about their own situation (e.g. eligibility, documents); never use user data to fill gaps about TUM programs. |
| **DEGREE AND INTERNATIONAL STUDENT RULES** | High school → Bachelor only; university → Master; tailor to international vs domestic when context allows; ask a short follow-up if unclear. |
| **CRITICAL RULES** | Only discuss programs in the context; only list requirements from the context (e.g. ✅/❌); when you don’t know, say so and redirect; when you do know, state it confidently. |
| **RESPONSE FORMAT** | Short questions → 2–4 sentences; lists → bullets; missing info → say what you don’t know + redirect; **no sign-offs** (no “Best regards”, “Sincerely”, “[Your Name]”). |

The **human message** then adds: the full CONTEXT (three sections), RECENT CONVERSATION (last 24 messages), STUDENT’S QUESTION, and a short “CRITICAL REMINDERS” block that repeats the main rules (only use context, state facts when you have them, redirect only when you don’t, no sign-offs, concise and confident).

### 6.2 How the system prompt improves results

| Goal | How the prompt achieves it |
|------|----------------------------|
| **Grounding and no hallucination** | ABSOLUTE RULE and INFORMATION HIERARCHY force the model to use only the provided context. “Never guess, assume, infer” and “NEVER invent deadlines, requirements…” reduce invented facts. |
| **Safe, consistent redirects** | ALLOWED REDIRECTS ONLY restricts outbound links to TUMonline and study@tum.de. Forbidden phrases are also removed in post-processing (`_sanitize_redirects`). |
| **Confident when we have the answer** | “WHEN YOU HAVE THE INFORMATION — BE CONFIDENT” and the human reminders tell the model to state dates/requirements directly when they are in the context, and not to hedge or redirect for that same information. |
| **Clear when we don’t** | “WHEN YOU DON’T KNOW” and “WHEN YOU ARE UNCERTAIN” ensure a direct “I don’t have that specific information” plus study@tum.de, without over-apologizing. |
| **Better follow-ups** | “WHEN TO ASK FOLLOW-UP QUESTIONS” encourages one or two short, concrete questions when the question is ambiguous, and then a complete answer using conversation history. |
| **Relevant use of user data** | “WHEN TO USE USER DATA” and “WHEN INFORMATION OR DOCUMENTS ARE MISSING” ensure profile and documents are used only for the student’s own situation and that missing profile/documents are clearly called out and improved over time. |
| **Consistent tone and format** | COMMUNICATION STYLE and RESPONSE FORMAT keep answers concise, direct, and without sign-offs or meta-mentions of “context”/“documents”, so the assistant sounds natural and professional. |
| **Eligibility-aware advice** | DEGREE AND INTERNATIONAL STUDENT RULES align answers with high school vs university and international vs domestic, using only what appears in the context. |

Together, the system prompt and the structured context (profile + user docs + TUM program chunks) make the RAG pipeline **retrieval-driven** and **prompt-driven**: retrieval selects what the model can use, and the prompt enforces how it uses it (grounding, redirects, confidence, and format).

---

## 7. Pipeline and Agent flow (technical summary)

1. **Input**: User question, optional `user_id`, optional `chat_history`.
2. **Guard**: Prompt-injection check; if detected, return fixed rejection message.
3. **Profile**: If `user_id`, fetch profile from Supabase (users, education, preferences).
4. **Plan**: LLM or heuristic decides actions: e.g. `fetch_profile`, `fetch_user_docs`, `search_kb`, `search_user_docs`, `answer`.
5. **Retrieval query**: Optionally augment question with chat context for follow-ups (`_query_for_retrieval`).
6. **KB search**: Embed query, optionally expand for keywords, call `hybrid_search_uni_degree_documents` with `filter_degree_level` (e.g. bachelor/master from profile or question). Filter by `hybrid_score >= 0.30`, take top k.
7. **User-doc search**: If `user_id`, call `hybrid_search_user_documents`; if empty, optionally fetch user docs from Storage, parse, build FAISS, similarity search.
8. **Context**: `compile_context_text(profile, kb_docs, user_docs)` → three sections (USER PROFILE, USER DOCUMENTS, TUM PROGRAM INFORMATION).
9. **Answer**: System prompt + context + chat history + question → LLM (Groq). Post-process: sanitize redirects (only study@tum.de / TUMonline), strip sign-offs.

---

## 8. Configuration reference (code)

Central place: **`backend/src/rag/chatbot/config.py`**.

| Constant | Default | Description |
|----------|--------|-------------|
| `GROQ_MODEL` | `meta-llama/llama-4-scout-17b-16e-instruct` | Groq model name. |
| `EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | HuggingFace embedding model. |
| `CHUNK_SIZE` | `500` | Chunk size (characters). |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks. |
| `RETRIEVAL_K` | `15` | Number of chunks to retrieve (KB). |
| `SIMILARITY_THRESHOLD` | `0.30` | Minimum hybrid score for KB chunks. |
| `SEMANTIC_WEIGHT` | `0.6` | Weight for semantic part of hybrid score. |
| `KEYWORD_WEIGHT` | `0.4` | Weight for keyword part of hybrid score. |

Pipeline and Agent are initialized with these (or overrides from `initialize_rag_pipeline` / `RAGChatbotPipeline` constructor).

---

## 9. Database and RPCs (RAG)

| Object | Type | Role |
|--------|------|------|
| `rag_uni_degree_documents` | Table | Stores KB chunks: `content`, `embedding` (vector 384), `metadata`; generated columns `university`, `degree`, `degree_level`. |
| `hybrid_search_uni_degree_documents` | RPC | Hybrid search over above table; params: `query_embedding`, `query_text`, `match_count`, `semantic_weight`, `keyword_weight`, optional filters. |
| `rag_user_documents` | Table | User doc chunks: `user_id`, `content`, `embedding`, `metadata`, `doc_type`. |
| `hybrid_search_user_documents` | RPC | Hybrid search over user docs; params: `p_user_id`, `query_embedding`, `query_text`, `match_count`, weights. |
| `rag_user_profile_chunks` | Table | Embedded profile summary per user. |
| `list_unique_degree_programs` | RPC | Returns distinct degree programs for “list all programs” and filtering. |

---

## 10. Python and library versions (RAG-relevant)

From `backend/requirements.txt` and usage:

| Package | Role |
|---------|------|
| `langchain`, `langchain-core`, `langchain-community`, `langchain-text-splitters` | Pipeline, prompts, document handling, splitters. |
| `langchain-groq` | ChatGroq LLM. |
| `langchain-huggingface` | HuggingFace embeddings. |
| `sentence-transformers` | Embedding model runtime. |
| `faiss-cpu` | FAISS in-memory vector store (user-doc fallback). |
| `supabase` | DB and RPC client. |
| `pymupdf` | PDF text extraction (user docs + ingestion fallback). |
| `docling` (optional) | Alternative PDF parser with OCR (used in Agent when available). |
| `numpy` | MMR and similarity computations in Agent (e.g. FAISS fallback path). |

---

## 11. Summary table (quick reference)

| Item | Value |
|------|--------|
| **LLM** | Groq, `meta-llama/llama-4-scout-17b-16e-instruct` |
| **LLM temperature** | 0 |
| **LLM max tokens** | 1000 |
| **Embedding model** | `paraphrase-multilingual-MiniLM-L12-v2` |
| **Embedding dimension** | 384 |
| **Chunk size / overlap** | 500 / 50 |
| **Retrieval k** | 15 |
| **KB fetch size** | k × 3, then filter by threshold |
| **Similarity threshold** | 0.30 (KB), slightly lower for user docs |
| **Hybrid weights** | Semantic 0.6, keyword 0.4 |
| **Retrieval** | Supabase hybrid (cosine + FTS, rank-normalized) |
| **Vector store** | Supabase pgvector (FAISS only as user-doc fallback) |

For high-level RAG flow and Agent behavior, see **README-RAG-CHATBOT.md**. For Supabase schema, see **README-SUPABASE-TABLES.md**.
