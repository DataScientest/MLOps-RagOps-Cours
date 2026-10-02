import asyncio
from pathlib import Path

from langchain_core.documents import Document

from app.services.pdf_processor import PDFProcessor

PDF = Path(__file__).resolve().parents[2] / "pdf_files" / "autoencoders.pdf"


def test_pdf_is_split_into_langchain_documents():
    chunks = asyncio.run(PDFProcessor().process_pdf(str(PDF), {"course": "ragops"}))

    assert chunks and all(isinstance(c, Document) for c in chunks)
    first = chunks[0]
    assert first.metadata["page_number"] == 1
    assert first.metadata["file_type"] == "pdf"
    assert first.metadata["course"] == "ragops"
    assert first.metadata["total_pages"] >= max(c.metadata["page_number"] for c in chunks)
    assert all(len(c.page_content) <= 500 for c in chunks)
