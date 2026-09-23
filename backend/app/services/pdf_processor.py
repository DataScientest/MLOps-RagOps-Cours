from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import hashlib
from typing import List, Optional
import os
from app.core.logging import logger 

class PDFProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def process_pdf(self, file_path: str, metadata: dict = None, source_name: Optional[str] = None) -> List[Document]:
        # source_name: original file name, so that re-ingesting the same PDF gives the same chunk ids
        source = source_name or file_path
        reader = PdfReader(file_path)
        pages = [page.extract_text() or "" for page in reader.pages]
        
        pdf_metadata = {
            "source": source,
            "total_pages": len(pages),
            "file_type": "pdf",
            **(metadata or {})
        }
        
        chunks = []
        for page_num, page_text in enumerate(pages):
            page_chunks = self.text_splitter.split_text(page_text)
            
            # Log pour comprendre le chunking
            logger.info(f"Processing page {page_num+1}/{len(pages)}: {len(page_chunks)} chunks created")
            for idx, c in enumerate(page_chunks[:2]):  # montrer un aperçu des 2 premiers chunks
                logger.info(f"Page {page_num+1} chunk {idx}: {c[:80]}...")

            for chunk_idx, chunk_text in enumerate(page_chunks):
                chunk_id = hashlib.md5(f"{source}_{page_num}_{chunk_idx}".encode()).hexdigest()
                chunks.append(Document(
                    page_content=chunk_text,
                    metadata={
                        **pdf_metadata,
                        "page_number": page_num + 1,
                        "chunk_index": chunk_idx,
                        "chunk_id": chunk_id
                    }
                ))
        logger.info(f"PDF {source} processed: {len(chunks)} chunks in total")
        return chunks
