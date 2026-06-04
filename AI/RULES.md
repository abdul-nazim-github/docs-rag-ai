## Code Style

- Use Python type hints for public APIs.
- Keep retrieval logic in `vector_store.py` and `rag_chain.py`; avoid duplicated
  similarity search code elsewhere.
- No hardcoded secrets. Use `app/core/config.py`.

## RAG Architecture Rules

- Always retrieve before generating. The chain in `rag_chain.py` enforces this.
- Preserve citations and `source` metadata on Document chunks.
- Keep chunk identifiers and metadata fields intact when modifying processing.

## Architectural Decisions (project-specific)

### FAISS (local)
Reason: simple, embeddable local store, persisted on disk.
Impact: keep index save/load API compatible and avoid reformatting vectors.

### OpenAI Embeddings
Reason: project uses `OpenAIEmbeddings` via langchain-openai.
Impact: embedding calls are external; watch rate limits and cost.

### RecursiveCharacterTextSplitter
Reason: balances chunk size and semantic boundaries for documents.
Impact: chunk_size=1000, chunk_overlap=200. Changing these affects recall and token usage.

## Fragile Areas

| File | Risk | Safe Strategy |
| ---- | ---- | ------------- |
| backend/app/services/vector_store.py | FAISS persistence and embedding calls | Don't change save/load format; if reindexing required, provide migration script. |
| backend/app/services/document_processor.py | Chunk size/overlap | Evaluate recall before changing; update tests. |
| backend/app/services/rag_chain.py | Prompt template & generation flow | Prompt edits can shift hallucination behavior — review with QA. |

## Scope Guard

Allowed:

- Small, focused bug fixes within the files listed in FILE_MAP.md.
- Adding logging, types, and small refactors that don't change behavior.

Not Allowed (without explicit approval):

- Replacing FAISS with another vector DB.
- Switching embedding model or changing vector dimension.
- Overhauling the prompt or retrieval order.

## Never Do

- Bypass the retriever and call LLM directly with user question.
- Remove the `source` metadata or citation mechanism.

## Always Do

- Make the smallest safe change required to fix a bug.
- Explain RAG impact in PR descriptions.
- Add tests for chunking, embedding integration, and registry updates for any change.

## Engineering Priorities

1. Retrieval accuracy
2. Correctness
3. Maintainability
4. Token & cost efficiency
