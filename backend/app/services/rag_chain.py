"""
RAG chain — retrieves relevant context and generates an answer via OpenAI.

Uses LangChain's chain composition to:
1. Retrieve top-k document chunks from the FAISS vector store.
2. Format them into a prompt alongside the user question.
3. Send the prompt to OpenAI and return the answer with source citations.
"""

from __future__ import annotations

import logging

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.vector_store import vector_store_manager

logger = logging.getLogger(__name__)

# ── Prompt template ────────────────────────────────────────────────────────────
RAG_PROMPT_TEMPLATE = """\
You are a knowledgeable assistant. Answer the user's question based ONLY on the
provided context. If the context does not contain enough information to answer
the question, say so clearly — do not make up information.

Context:
{context}

Question: {question}

Answer:"""


class RAGChain:
    """Orchestrates retrieval-augmented generation."""

    def __init__(self) -> None:
        self._llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.3,
        )
        self._prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        self._output_parser = StrOutputParser()

    # ── Public API ─────────────────────────────────────────────────────────────

    async def query(self, question: str, k: int = 4) -> dict:
        """
        Run the full RAG pipeline: retrieve → prompt → generate.

        Args:
            question: The user's natural-language question.
            k: Number of context chunks to retrieve.

        Returns:
            Dict with keys:
                - answer (str): The generated answer.
                - sources (list[dict]): Source chunks used for the answer.
        """
        if not vector_store_manager.is_ready:
            return {
                "answer": (
                    "No documents have been uploaded yet. "
                    "Please upload at least one document before asking questions."
                ),
                "sources": [],
            }

        logger.info("RAG query: %s (k=%d)", question, k)

        # Retrieve relevant chunks
        retriever = vector_store_manager.get_retriever(k=k)
        relevant_docs: list[Document] = retriever.invoke(question)

        # Format context
        context = self._format_context(relevant_docs)

        # Build and invoke the chain
        chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | self._prompt
            | self._llm
            | self._output_parser
        )

        answer = await chain.ainvoke(
            {"context": context, "question": question}
        )

        # Extract unique sources
        sources = self._extract_sources(relevant_docs)

        logger.info("Generated answer with %d source(s).", len(sources))
        return {"answer": answer, "sources": sources}

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _format_context(documents: list[Document]) -> str:
        """Join document chunks into a single context string."""
        parts: list[str] = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "unknown")
            parts.append(f"[Source {i}: {source}]\n{doc.page_content}")
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _extract_sources(documents: list[Document]) -> list[dict]:
        """Deduplicate and return source metadata."""
        seen: set[str] = set()
        sources: list[dict] = []
        for doc in documents:
            source_name = doc.metadata.get("source", "unknown")
            if source_name not in seen:
                seen.add(source_name)
                sources.append(
                    {
                        "filename": source_name,
                        "snippet": doc.page_content[:200] + "…"
                        if len(doc.page_content) > 200
                        else doc.page_content,
                    }
                )
        return sources


# ── Module-level singleton ─────────────────────────────────────────────────────
rag_chain = RAGChain()
