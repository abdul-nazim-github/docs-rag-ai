## PDF Ingestion

Files:

- backend/app/services/document_processor.py
	- Purpose: Load PDFs/DOCX/TXT/MD and produce semantically split Document chunks.

## Chunking

Files:

- backend/app/services/document_processor.py  (RecursiveCharacterTextSplitter)
	- Purpose: Controls chunk_size and overlap; central for token efficiency and recall.

## Embeddings

Files:

- backend/app/services/vector_store.py  (OpenAIEmbeddings via langchain-openai)
	- Purpose: Wraps OpenAIEmbeddings used to vectorize text chunks.

## Vector Store

Files:

- backend/app/services/vector_store.py  (FAISS local index, save_local/load_local)
	- Purpose: Manages FAISS index lifecycle: create, save_local, load_local, reset.

## Retriever

Files:

- backend/app/services/vector_store.py  (as_retriever)
- backend/app/services/rag_chain.py      (uses retriever.get_retriever)
	- Purpose: Exposes a LangChain retriever (k configurable) used by RAG chain.

## Prompt Builder

Files:

- backend/app/services/rag_chain.py  (RAG_PROMPT_TEMPLATE)
	- Purpose: Contains the prompt template guaranteeing retrieval-before-generation.

## LLM Interface

Files:

- backend/app/services/rag_chain.py  (ChatOpenAI via langchain-openai)
	- Purpose: Instantiates ChatOpenAI with settings.OPENAI_MODEL and calls the chain.

## API Layer

Files:

- backend/app/api/routes.py
- backend/app/api/schemas.py
	- Purpose: HTTP endpoints for upload/query/list/delete; pydantic request/response models.

## Document Registry

Files:

- backend/app/services/document_service.py (data/documents.json management)
	- Purpose: Manages `data/documents.json`, uploads on-disk files, and triggers indexing.

## Config

Files:

- backend/app/core/config.py
	- Purpose: Loads env variables (OPENAI_API_KEY, model, paths) and computes absolute paths.

## Utilities / Supported loaders

Files:

- backend/app/services/document_processor.py (PyPDFLoader, TextLoader, UnstructuredMarkdownLoader, DOCX loader)
	- Purpose: Concrete loaders used by `DocumentProcessor` to extract raw text sections.

## Fragile files (high-risk to change)

- backend/app/services/vector_store.py ⚠️ fragile  (FAISS persistence & embeddings)
- backend/app/services/document_processor.py ⚠️ fragile  (chunking sizes & splitters)
- backend/app/services/rag_chain.py ⚠️ fragile  (prompt template, generation flow)

When modifying fragile files: document the reason, expected RAG impact, and add
regression tests for retrieval accuracy before merging.
