from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_processor import PDFProcessor
from app.services.ingestion import ingest_documents
import tempfile, os, logging
from typing import List, Optional
from app.models.documents import Document

router = APIRouter()
logger = logging.getLogger(__name__)
pdf_processor = PDFProcessor()

@router.post("/ingest-pdf-batch")
async def ingest_pdf_batch(files: List[UploadFile] = File(...), metadata: Optional[dict] = None):
    results = []
    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"Only PDF files supported: {file.filename}")
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name

            documents = await pdf_processor.process_pdf(tmp_path, metadata, source_name=file.filename)
            ragops_docs = [
            Document(id=doc.metadata["chunk_id"], text=doc.page_content, metadata=doc.metadata) for doc in documents]
            result = await ingest_documents(ragops_docs)
            os.unlink(tmp_path)

            results.append({
                "filename": file.filename,
                "pages_processed": max(doc.metadata["page_number"] for doc in documents),
                "chunks_created": len(documents),
                **result
            })
        except Exception as e:
            logger.error(f"Ingestion failed for {file.filename}: {str(e)}")
            results.append({"filename": file.filename, "error": str(e)})
    return results
