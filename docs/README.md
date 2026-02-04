# Teduco — Product Presentation Docs

This folder contains **overview and workflow** documentation for product presentations. Each README includes:

- **Diagrams for non-technical audiences** — Plain-language flows and tables (no jargon); use these with stakeholders, product owners, or non-developers.
- **Technical diagrams** — Architecture and detailed workflows (Mermaid + ASCII) for developers.

---

## Documents

| Document | Content |
|----------|--------|
| **[README-BACKEND.md](./README-BACKEND.md)** | Backend: what the server does in plain terms + request/action tables; then technical routers, flows, component layout. |
| **[README-RAG-CHATBOT.md](./README-RAG-CHATBOT.md)** | Chat assistant: what it uses to answer (TUM info, your profile, your documents), simple Q→A flow, who sees which programs; then technical Agent flow. |
| **[README-RAG-PIPELINE-TECHNICAL.md](./README-RAG-PIPELINE-TECHNICAL.md)** | **RAG pipeline technical reference:** models (LLM, embeddings), top-k, retrieval (hybrid search, threshold), chunking, config, tech stack, DB/RPCs. |
| **[README-FRONTEND.md](./README-FRONTEND.md)** | Frontend: screens and user journey, what happens when you send a message, where data lives; then technical routes, hooks, API flow. |
| **[README-SUPABASE-TABLES.md](./README-SUPABASE-TABLES.md)** | Data storage: what we store (account, profile, documents, chats, TUM info), how it’s used, who can see what; then technical tables and RPCs. |

---

## How to use

- **Non-developers**: Start with **Section 2 — Diagrams for non-technical audiences** in each README. Use the simple flowcharts and tables for slides or handouts.
- **Slides**: Copy the ASCII diagrams from Section 2 (or the Mermaid/ASCII from the technical sections) into your deck, or render Mermaid via [Mermaid Live](https://mermaid.live) or your editor.
- **Narrative**: Use “Overview” and “Summary for presentation” in each README as talking points.
- **Developers**: Use the “Detailed workflow (technical)” sections and file layout when explaining implementation.

For full architecture and patterns (unified backend, naming, React Query, etc.), see the root **ARCHITECTURE.md**.
