import logging
from pathlib import Path
from typing import List, Optional

from langchain.docstore.document import Document
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)

from app.retriever import VectorStoreManager
from app.utils import clean_text, discover_supported_files, get_text_splitter


logger = logging.getLogger(__name__)


class DocumentIngestor:
    """Loads source documents, chunks them, and stores embeddings."""

    def __init__(self) -> None:
        self.text_splitter = get_text_splitter()
        self.vectorstore = VectorStoreManager()

    def _load_file(self, file_path: Path) -> List[Document]:
        """Select the correct loader based on file extension."""
        suffix = file_path.suffix.lower()
        logger.info("Loading file: %s", file_path)

        if suffix == ".pdf":
            loader = PyPDFLoader(str(file_path))
        elif suffix == ".txt":
            loader = TextLoader(str(file_path), encoding="utf-8")
        elif suffix == ".docx":
            loader = Docx2txtLoader(str(file_path))
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        return loader.load()

    def load_documents(self, paths: Optional[List[str]] = None) -> List[Document]:
        """Load all supported documents from explicit paths or the data directory."""
        files = discover_supported_files(paths)
        if not files:
            raise FileNotFoundError(
                "No supported files found. Add PDF, TXT, or DOCX files to the data directory."
            )

        documents: List[Document] = []
        for file_path in files:
            loaded_docs = self._load_file(file_path)
            for doc in loaded_docs:
                doc.page_content = clean_text(doc.page_content)
                doc.metadata["source"] = str(file_path)
            documents.extend(loaded_docs)

        logger.info("Loaded %s raw document(s)", len(documents))
        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller chunks to improve retrieval accuracy."""
        logger.info("Chunking %s document(s)", len(documents))
        chunks = self.text_splitter.split_documents(documents)
        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = index
        logger.info("Created %s chunk(s)", len(chunks))
        return chunks

    def ingest(self, paths: Optional[List[str]] = None) -> dict:
        """Execute the full ingestion pipeline from load to vector persistence."""
        documents = self.load_documents(paths)
        chunks = self.chunk_documents(documents)
        self.vectorstore.create_or_replace(chunks)

        unique_sources = sorted({doc.metadata.get("source", "unknown") for doc in chunks})
        return {
            "documents_loaded": len(documents),
            "chunks_created": len(chunks),
            "sources": unique_sources,
        }
