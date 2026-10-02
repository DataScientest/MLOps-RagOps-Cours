from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_processor import PDFProcessor
from app.services.ingestion import ingest_documents
from app.models.documents import Document  # 👈 your pipeline model
import tempfile, os, logging
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)
pdf_processor = PDFProcessor()

@router.post("/ingest-pdf")
async def ingest_pdf(file: UploadFile = File(...), metadata: Optional[dict] = None):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files supported")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Process into LangChain Documents
        lc_documents = await pdf_processor.process_pdf(tmp_path, metadata, source_name=file.filename)

        # Convert LangChain Document -> RagopsDocument
        ragops_docs = [
            Document(
                id=doc.metadata["chunk_id"],       # unique id
                text=doc.page_content,             # full text chunk
                metadata=doc.metadata              # dict of extra metadata
            )
            for doc in lc_documents
        ]

        result = await ingest_documents(ragops_docs)

        os.unlink(tmp_path)

        return {
            "filename": file.filename,
            "pages_processed": max(doc.metadata["page_number"] for doc in lc_documents),
            "chunks_created": len(lc_documents),
            **result
        }

    except Exception as e:
        logger.error(f"PDF ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")
