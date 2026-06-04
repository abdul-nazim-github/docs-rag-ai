import sys
import types
import pytest

# --- Inject lightweight stubs for external langchain packages so tests do not
# require third-party packages or an OpenAI API key at import time.
fake_openai = types.ModuleType("langchain_openai")

class DummyOpenAIEmbeddings:
    def __init__(self, *args, **kwargs):
        # no-op; used only to satisfy constructor signature
        pass

fake_openai.OpenAIEmbeddings = DummyOpenAIEmbeddings
sys.modules["langchain_openai"] = fake_openai

# Stub for langchain_community.vectorstores.FAISS
fake_lc_comm = types.ModuleType("langchain_community")
fake_vectorstores = types.ModuleType("langchain_community.vectorstores")

class DummyFAISS:
    def __init__(self):
        self.index = types.SimpleNamespace(ntotal=0)

    @staticmethod
    def load_local(path, embeddings, allow_dangerous_deserialization=False):
        # Simulate missing on-disk index by returning None-like behavior (raise)
        raise FileNotFoundError

    @staticmethod
    def from_documents(documents, embeddings):
        inst = DummyFAISS()
        inst.index.ntotal = len(documents)
        return inst

    def add_documents(self, documents):
        self.index.ntotal += len(documents)

    def save_local(self, path):
        return None

    def as_retriever(self, search_kwargs=None):
        class Retriever:
            def __init__(self, store):
                self._store = store

            def invoke(self, query):
                return []

        return Retriever(self)

    def similarity_search(self, query, k=4):
        return []

fake_vectorstores.FAISS = DummyFAISS
sys.modules["langchain_community"] = fake_lc_comm
sys.modules["langchain_community.vectorstores"] = fake_vectorstores

# Stub langchain_core.documents.Document used for typing
fake_lc_core = types.ModuleType("langchain_core")
fake_docs_mod = types.ModuleType("langchain_core.documents")

class DummyDocument:
    def __init__(self, page_content="", metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

fake_docs_mod.Document = DummyDocument
sys.modules["langchain_core"] = fake_lc_core
sys.modules["langchain_core.documents"] = fake_docs_mod

# Now import the real vector_store_manager with stubs in place
from app.services.vector_store import vector_store_manager


def test_reset_clears_index(tmp_path):
    """Reset should clear any loaded index and set document_count to 0."""
    # Ensure reset is idempotent
    vector_store_manager.reset()
    assert not vector_store_manager.is_ready
    assert vector_store_manager.document_count == 0


def test_similarity_search_raises_when_empty():
    """similarity_search should raise a RuntimeError when no index is available."""
    vector_store_manager.reset()
    with pytest.raises(RuntimeError):
        vector_store_manager.similarity_search("test query", k=1)
