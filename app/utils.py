import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter


load_dotenv()


def setup_logging() -> None:
    """Configure application-wide structured logging once."""
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


setup_logging()


logger = logging.getLogger("qa-system")


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


@dataclass(frozen=True)
class Settings:
    """Centralized runtime settings loaded from environment variables."""

    app_name: str = os.getenv("APP_NAME", "LLM Question Answering System")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    data_dir: str = os.getenv("DATA_DIR", "data")
    vectorstore_dir: str = os.getenv("VECTORSTORE_DIR", "vectorstore")
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")
    llm_model: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    top_k: int = int(os.getenv("TOP_K", "4"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.2"))
    max_chat_history: int = int(os.getenv("MAX_CHAT_HISTORY", "5"))
    cors_origins: List[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",")
            if origin.strip()
        ]
    )


settings = Settings()


def ensure_directories() -> None:
    """Create required directories so ingestion and persistence do not fail."""
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.vectorstore_dir).mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    """Normalize whitespace and remove noisy characters from text."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s.,?!:/@#&()'\"-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize_text(text: str) -> List[str]:
    """Simple regex tokenizer used during preprocessing and metrics."""
    return re.findall(r"\b\w+\b", text.lower())


def preprocess_query(query: str) -> dict:
    """Clean and tokenize the incoming user query."""
    cleaned_query = clean_text(query)
    tokens = tokenize_text(cleaned_query)
    return {
        "original_query": query,
        "cleaned_query": cleaned_query,
        "tokens": tokens,
        "token_count": len(tokens),
    }


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Shared splitter configuration for all ingested documents."""
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def supported_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def discover_supported_files(paths: Optional[Iterable[str]] = None) -> List[Path]:
    """Resolve file paths from explicit inputs or by scanning the data directory."""
    if paths:
        resolved_paths = [Path(path).resolve() for path in paths]
    else:
        resolved_paths = [
            path.resolve()
            for path in Path(settings.data_dir).glob("**/*")
            if path.is_file()
        ]

    files = [path for path in resolved_paths if supported_file(path)]
    logger.info("Discovered %s supported document(s)", len(files))
    return files


def simple_precision_at_k(retrieved_chunks: List[str], query_tokens: List[str]) -> float:
    """Toy retrieval metric for debugging relevance quality."""
    if not retrieved_chunks or not query_tokens:
        return 0.0

    relevant = 0
    for chunk in retrieved_chunks:
        chunk_tokens = set(tokenize_text(chunk))
        if any(token in chunk_tokens for token in query_tokens):
            relevant += 1
    return relevant / len(retrieved_chunks)
