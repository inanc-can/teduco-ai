# Teduco RAG Chatbot — Overview & Workflow

**Product presentation reference.**  
RAG (Retrieval-Augmented Generation) chatbot: planning, retrieval (KB + user docs), and answer generation for TUM admissions.

---

## 1. Overview

The RAG chatbot answers user questions using:

1. **TUM program information** — University degree documents stored and searched in Supabase (hybrid semantic + keyword).
2. **User profile** — From Supabase (users, education, preferences); used for eligibility (e.g. Bachelor vs Master) and personalization.
3. **User documents** — Uploaded files (transcript, diploma, CV, etc.) chunked, embedded, and stored in Supabase; searched when the user asks about their own situation.

The **Agent** decides which sources to use, runs retrieval, and the **LLM** (Groq) produces a short, precise answer grounded only in the provided context.

### High-level RAG architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RAG CHATBOT                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Entry points:                                                               │
│  • POST /chats/{id}/messages  (database-backed chat, user_id from JWT)       │
│  • POST /chat                 (standalone, optional Authorization)            │
├─────────────────────────────────────────────────────────────────────────────┤
│  RAGChatbotPipeline (pipeline.py)                                            │
│  ├── DocumentLoader, RetrievalPipeline (embeddings, chunking config)         │
│  ├── LLM: ChatGroq                                                           │
│  └── Agent (agent.py) ◄── main orchestration                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  Agent                                                                       │
│  ├── plan_actions(question, profile_summary) → [fetch_profile, fetch_user_   │
│  │   docs, search_kb, search_user_docs, answer]                              │
│  ├── fetch_user_profile(user_id) → Supabase users + education + preferences  │
│  ├── fetch_user_documents(user_id) → download from Storage, parse PDF/text  │
│  ├── search_kb(question, profile) → Supabase hybrid_search_uni_degree_docs  │
│  ├── search_user_docs_supabase(question, user_id) → hybrid_search_user_docs  │
│  ├── compile_context_text(profile, kb_docs, user_docs)                        │
│  └── final_answer(question, profile, kb_docs, user_docs, chat_history) → LLM │
└─────────────────────────────────────────────────────────────────────────────┘
         │                    │                          │
         ▼                    ▼                          ▼
   Supabase (profile)   Supabase (rag_uni_degree_documents,   Supabase (rag_user_documents,
   users, education,   hybrid_search_uni_degree_documents)   hybrid_search_user_documents)
   onboarding_prefs
```

---

## 2. Diagrams for non-technical audiences

*Use these when presenting to stakeholders, product owners, or non-developers.*

### What the assistant uses to answer you

The chat assistant does **not** invent answers. It only uses three kinds of information that Teduco manages for you:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  SOURCES THE ASSISTANT USES                                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ① TUM PROGRAM INFORMATION         Official TUM degree info (requirements,       │
│     (always available)             deadlines, application steps).               │
│                                                                                  │
│  ② YOUR PROFILE                    What you entered: high school or university,  │
│     (if you’re logged in)          GPA, target programs, etc.                   │
│                                                                                  │
│  ③ YOUR UPLOADED DOCUMENTS         Transcript, diploma, CV — so the assistant  │
│     (if you uploaded any)           can say what you have or still need.         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### How your question becomes an answer (simple flow)

```
  YOU ASK                          SYSTEM                                  YOU GET
  ───────                          ──────                                  ───────

  "What do I need                   1. Understands your question
   for Informatics                  2. Looks up TUM program info
   Master?"                         3. If you’re logged in: checks your
       │                               profile and your documents
       │                            4. Writes an answer using ONLY
       │                               that information (no guessing)
       │                                    │
       └───────────────────────────────────┼───────────────────────────────►
                                           │
                                    "For Informatics MSc you need …
                                     Based on your transcript you
                                     already have … You still need …"
```

### Who sees which programs?

So answers stay relevant, the assistant only suggests programs that fit your situation:

```
  IF YOU’RE IN HIGH SCHOOL              IF YOU’RE AT / FINISHED UNIVERSITY
  ─────────────────────────              ─────────────────────────────────
  You see: BACHELOR programs only        You see: MASTER programs
  (e.g. BSc Informatics)                 (e.g. MSc Informatics, MSc Data Science)
  Master’s is for after a first degree   You can also ask about Bachelor’s if you want
```

### When the assistant doesn’t know

The assistant is not allowed to guess. If the answer isn’t in TUM program info or your profile/documents:

```
  Your question                    What happens                         Answer you get
  ─────────────                    ─────────────                         ─────────────
  Something specific               Assistant looks in TUM info          "I don’t have that
  (e.g. a detail not in            and your data — not there            specific information.
  our system)                                                             Please contact
                                                                         study@tum.de for details."
```

---

## 3. Detailed workflow diagrams (technical)

### 3.1 End-to-end: from user message to assistant reply

```mermaid
flowchart TB
    subgraph Input
        Q[User question]
        UID[user_id optional]
        HIST[chat_history]
    end

    subgraph Guard
        G[Input guard: prompt injection check]
    end

    subgraph Plan
        P[plan_actions: LLM or heuristic → actions]
        RS[retrieval_question = query_for_retrieval with chat history]
    end

    subgraph Fetch
        FP[fetch_user_profile if user_id]
        FU[search_user_docs_supabase or fetch_user_documents + search_user_docs]
    end

    subgraph Search_KB
        SKB[search_kb: degree_level filter, embed query, expand query]
        HYB[Supabase: hybrid_search_uni_degree_documents]
    end

    subgraph Answer
        CT[compile_context_text: USER PROFILE + USER DOCUMENTS + TUM PROGRAM INFO]
        FA[final_answer: system prompt + context + chat_history + question]
        LLM[ChatGroq]
        SAN[sanitize_redirects, strip_sign_off]
    end

    Q --> G
    G --> FP
    FP --> P
    Q --> P
    P --> RS
    RS --> SKB
    P --> FU
    SKB --> HYB
    HYB --> CT
    FU --> CT
    FP --> CT
    CT --> FA
    HIST --> FA
    FA --> LLM
    LLM --> SAN
    SAN --> OUT[Assistant reply]
```

### 3.2 Agent run sequence (detailed)

```mermaid
sequenceDiagram
    participant Caller
    participant Agent
    participant DB
    participant SupabaseRAG
    participant LLM

    Caller->>Agent: run(question, user_id, chat_history)
    Agent->>Agent: _detect_prompt_injection(question)
    alt Injection detected
        Agent-->>Caller: REJECTION_MESSAGE
    end

    Agent->>DB: fetch_user_profile(user_id)
    DB-->>Agent: profile

    Agent->>Agent: plan_actions(question, profile_summary)
    Agent-->>Agent: actions

    Agent->>Agent: _query_for_retrieval(question, chat_history)
    Agent-->>Agent: retrieval_question

    Agent->>SupabaseRAG: search_kb(retrieval_question, profile)
    Note over SupabaseRAG: degree_level filter, embed, expand query, hybrid search
    SupabaseRAG-->>Agent: kb_docs

    opt user_id
        Agent->>SupabaseRAG: search_user_docs_supabase(retrieval_question, user_id)
        SupabaseRAG-->>Agent: user_docs
        opt fallback if empty
            Agent->>DB: fetch_user_documents(user_id)
            Agent->>Agent: search_user_docs(question, raw_docs)
        end
    end

    Agent->>Agent: compile_context_text(profile, kb_docs, user_docs)
    Agent->>LLM: final_answer(question, profile, kb_docs, user_docs, chat_history)
    LLM-->>Agent: answer
    Agent->>Agent: _sanitize_redirects, _strip_sign_off
    Agent-->>Caller: answer
```

### 3.3 Knowledge base search (search_kb) flow

```mermaid
flowchart TB
    subgraph Input
        Q[question]
        P[profile]
    end

    subgraph List_programs
        L[List all programs? list_trigger + program_trigger]
        LP[list_all_degree_programs RPC]
        FLT[Filter by applicant_type: high-school→bachelor, university→master]
        DOC_LIST[Single Document: program list text]
    end

    subgraph Hybrid_search
        LV[degree_level from profile or question keywords]
        EMB[embed_query question]
        EXP[_expand_query synonyms for deadline, requirements, language, docs, fees]
        RPC[retrieve_chunks: hybrid_search_uni_degree_documents]
        THR[Filter by hybrid_score >= threshold]
        TOP[Take top k]
    end

    Q --> L
    L -->|Yes| LP --> FLT --> DOC_LIST
    L -->|No| LV --> EMB --> EXP --> RPC --> THR --> TOP
```

### 3.4 Context compilation and final answer

```mermaid
flowchart LR
    subgraph Context
        A[=== USER PROFILE ===]
        B[=== USER DOCUMENTS ===]
        C[=== TUM PROGRAM INFORMATION ===]
    end

    subgraph LLM_input
        S[System prompt: rules, redirects, style]
        CT[CONTEXT: A + B + C]
        CH[RECENT CONVERSATION]
        Q[STUDENT'S QUESTION]
    end

    A --> CT
    B --> CT
    C --> CT
    CT --> LLM_input
    S --> LLM_input
    LLM_input --> Groq
    Groq --> Post[Sanitize redirects, strip sign-off]
    Post --> Response
```

### 3.5 RAG module file layout

```mermaid
flowchart TB
    subgraph rag/
        pipeline[pipeline.py: RAGChatbotPipeline, initialize_rag_pipeline]
        agent[agent.py: Agent]
        config[config.py: GROQ_MODEL]
        loader[loader.py: DocumentLoader]
        retriever[retriever.py: RetrievalPipeline - embeddings, chunking]
        db_ops[db_ops.py: retrieve_chunks, list_all_degree_programs, retrieve_user_document_chunks, upsert_*]
    end
    subgraph rag/parser
        conversion[conversion.py: Docling PDF]
        pdf_parser[pdf_parser.py: PyMuPDF fallback]
        crawler[crawler.py: TUM scraper]
    end
    subgraph rag/chunker
        langchain_splitters[langchain_splitters.py: MarkdownHeaderSplitter]
    end

    pipeline --> agent & config & loader & retriever & db_ops
    agent --> db_ops & retriever
```

---

## 4. Key behaviors (for presentation)

| Topic | Behavior |
|-------|----------|
| **Planning** | LLM or heuristic chooses: fetch_profile, fetch_user_docs, search_kb, search_user_docs, answer. |
| **Eligibility** | High-school → Bachelor only; university → Master (or Bachelor if asked). Filters KB and program list. |
| **Retrieval** | Hybrid search (semantic + keyword) in Supabase for both university degree docs and user document chunks. |
| **Follow-ups** | `_query_for_retrieval` augments short/follow-up questions with context from recent chat (e.g. program name). |
| **Safety** | Prompt injection guard; only allowed redirects: study@tum.de and TUMonline (no “check TUM website”). |
| **Answer rules** | Only use provided context; no sign-offs; concise; use first name when available. |

---

## 5. Data sources summary

| Source | Table / storage | Used for |
|--------|-------------------|----------|
| User profile | users, high_school_education / university_education, onboarding_preferences | Eligibility, personalization, profile summary in context. |
| TUM programs | rag_uni_degree_documents + hybrid_search_uni_degree_documents | Deadlines, requirements, program info. |
| User documents | Storage bucket + documents table; rag_user_documents (chunks) + hybrid_search_user_documents | CV, transcript, diploma for “my eligibility” type questions. |

---

## 6. Related docs

- **README-BACKEND.md** — How chats and `/chat` call the RAG pipeline and Agent.
- **README-SUPABASE-TABLES.md** — Tables and RPCs used by the RAG chatbot (rag_uni_degree_documents, rag_user_documents, list_unique_degree_programs, hybrid search functions).
