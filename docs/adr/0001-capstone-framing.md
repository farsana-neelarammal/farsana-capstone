# ADR-0001: Capstone Framing — Laravel Docs RAG Assistant

- **Status:** Draft v1
- **Date:** 2026-10-11
- **Author:** Farsana

## Context

This capstone builds a retrieval-augmented generation system for Laravel documentation so developers can ask natural-language questions and get grounded answers from the official docs instead of relying on memory or scattered forum snippets. The target users are Laravel developers, teams evaluating framework features, and newer developers who need fast access to accurate API and framework guidance. This is relevant now because Laravel documentation is large, frequently updated, and difficult to search efficiently when developers are troubleshooting implementation details or comparing patterns.

## Decision — Solution Framing Canvas

| Box | Your answer |
|-----|-------------|
| **Inputs** | A question in plain English from a user, optionally with context such as a Laravel version, framework area (routing, validation, Eloquent, queueing, etc.), or a code snippet to anchor the query. |
| **Outputs** | A concise, grounded answer to the question, paired with relevant source passages or citations from the Laravel documentation and, where useful, a short list of recommended next steps or references. |
| **Tools** | The system uses Laravel documentation content as the source corpus, an embedding model to index and retrieve relevant passages, a vector database for similarity search, and an LLM to synthesize a final response grounded in the retrieved document chunks. |
| **Memory** | The system keeps only minimal conversational context within a single session, such as the last few turns, and stores durable knowledge in the indexed documentation corpus rather than long-lived user memory. |
| **Autonomy level** | This is a retrieval-augmented assistant rather than a fully autonomous agent. It decides which documents to retrieve and how to summarize them, but it does not independently modify code, browse the wider web, or act on external systems without explicit user direction. |
| **Decision boundaries** | The assistant is allowed to answer from the source corpus, rank relevant documentation, and ask clarifying questions when a request is ambiguous. It is not allowed to invent undocumented API behavior, claim certainty beyond the referenced docs, or take actions like making code changes or deploying services without human approval. |

## Consequences

- **Positive:**
  - Developers can get faster, more accurate answers grounded in Laravel documentation.
  - The system reduces reliance on vague memory or outdated external blog posts.
  - The architecture is modular and extensible for future improvements such as chunk tuning, version-aware retrieval, or better citation formatting.

- **Negative / risks:**
  - Retrieval quality depends heavily on document chunking, embeddings, and metadata quality.
  - The assistant may still produce overconfident answers if the query is under-specified or the documentation corpus is incomplete.
  - Version drift is a real risk, since Laravel changes over time and docs may differ across releases.

- **Things we'll re-visit:**
  - Whether the project should support multiple Laravel versions and how version-aware retrieval will be handled.
  - Whether answer quality needs stronger citation and grounding checks before the system is considered reliable enough for broader use.
