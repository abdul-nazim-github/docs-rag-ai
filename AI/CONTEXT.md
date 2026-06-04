## Purpose

This repository implements a PDF-focused Retrieval-Augmented Generation (RAG)
backend: ingest PDFs (and other document types), split into chunks, embed with
OpenAI embeddings, store vectors in a local FAISS index, then retrieve and
answer user questions via OpenAI (LangChain wrappers).

## Users

- Product engineers and AI agents that need programmatic access to uploaded
  documents via a query API.
- Human users via the frontend asking questions about uploaded PDFs.

## Tech Stack

- Python >= 3.11
- FastAPI (HTTP API)
- LangChain (chain composition + text splitting)
- langchain-openai (ChatOpenAI + OpenAIEmbeddings)
- OpenAI models (default: gpt-4.1-mini as configured)
- FAISS (local, persisted index)
- Loaders: PyPDFLoader, TextLoader, UnstructuredMarkdownLoader, python-docx

## RAG Pipeline (high-level)

PDF Upload
↓
Extraction (PyPDFLoader / loaders)
↓
Chunking (RecursiveCharacterTextSplitter: chunk_size=1000, overlap=200)
↓
Embedding (OpenAIEmbeddings)
↓
Vector Storage (FAISS local index)
↓
Retrieval (FAISS retriever, k configurable)
↓
Prompt Assembly (RAG_PROMPT_TEMPLATE in `app/services/rag_chain.py`)
↓
LLM Response (ChatOpenAI via LangChain)

## Hard Constraints

- Retrieval must occur before generation: never answer without context.
- Preserve source metadata and snippets for citations (filename, snippet).
- Do not change vector schema, vector dimension, or embedding model without
  explicit approval.
- No hard-coded secrets in code; keys come from `backend/.env` or environment
  variables. `app/core/config.py` validates them.

## Critical Business Logic

- Document upload -> process_file() -> create chunks with `source` metadata.
- Chunking parameters (1000/200) are tuned for token balance; changing them
  affects retrieval overlap and should be evaluated.
- The FAISS index is persisted at `vectorstore/faiss_index` and loaded at
  startup; missing index triggers a rebuild from `data/documents.json`.
