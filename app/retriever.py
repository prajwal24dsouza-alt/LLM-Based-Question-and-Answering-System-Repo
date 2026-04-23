import logging
from pathlib import Path
from typing import List, Optional

from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from app.utils import ensure_directories, settings


logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Encapsulates vector store creation, loading, and semantic retrieval."""

    def __init__(self) -> None:
        ensure_directories()
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self.vectorstore_path = Path(settings.vectorstore_dir)

    def create_or_replace(self, documents: List[Document]) -> None:
        """Build a FAISS index from chunks and persist it to disk."""
        if not documents:
            raise ValueError("No documents were provided to build the vector store.")

        logger.info("Creating vector store with %s document chunk(s)", len(documents))
        vectorstore = FAISS.from_documents(documents, self.embedding_model)
        vectorstore.save_local(str(self.vectorstore_path))
        logger.info("Vector store persisted to %s", self.vectorstore_path)

    def load(self) -> FAISS:
        """Load an existing vector store from disk."""
        index_file = self.vectorstore_path / "index.faiss"
        if not index_file.exists():
            raise FileNotFoundError(
                f"Vector store not found at {index_file}. Run ingestion first."
            )

        logger.info("Loading vector store from %s", self.vectorstore_path)
        return FAISS.load_local(
            str(self.vectorstore_path),
            self.embedding_model,
            allow_dangerous_deserialization=True,
        )

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Document]:
        """Perform semantic similarity search to fetch the most relevant chunks."""
        vectorstore = self.load()
        k = top_k or settings.top_k
        logger.info("Running similarity search with top_k=%s", k)
        return vectorstore.similarity_search(query, k=k)
