from pathlib import Path

from app.services.document_processor import DocumentProcessor


def test_process_txt_single_chunk(tmp_path: Path) -> None:
    """Processing a small text file should produce at least one chunk and attach source metadata."""
    p = tmp_path / "sample.txt"
    # Create a small text file
    p.write_text("Hello world. This is a test document.\n" * 20, encoding="utf-8")

    dp = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
    chunks = dp.process_file(p)

    assert isinstance(chunks, list)
    assert len(chunks) >= 1

    for doc in chunks:
        assert "source" in doc.metadata
        assert doc.metadata["source"] == p.name
        assert hasattr(doc, "page_content") and doc.page_content
