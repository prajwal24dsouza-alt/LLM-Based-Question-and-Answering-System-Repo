import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.ingestion import DocumentIngestor
from app.llm import LLMService
from app.retriever import VectorStoreManager
from app.utils import (
    ensure_directories,
    preprocess_query,
    settings,
    simple_precision_at_k,
)


logger = logging.getLogger(__name__)


app = FastAPI(title=settings.app_name, version=settings.app_version)
memory_store: Dict[str, List[Dict[str, str]]] = defaultdict(list)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    file_paths: Optional[List[str]] = Field(
        default=None,
        description="Optional absolute or relative file paths. Defaults to scanning the data directory.",
    )


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question asked by the user")
    top_k: int = Field(default=settings.top_k, ge=1, le=20)
    session_id: str = Field(default="default", description="Conversation session identifier")
    include_sources: bool = Field(default=True)


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question asked by the user")
    session_id: str = Field(default="default", description="Conversation session identifier")


@app.on_event("startup")
def startup_event() -> None:
    """Ensure required directories exist when the API starts."""
    ensure_directories()
    logger.info("Application startup complete")


@app.get("/health")
def health_check() -> dict:
    """Simple health endpoint for readiness checks."""
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> JSONResponse:
    """Save an uploaded PDF into the data directory and ingest it immediately."""
    try:
        logger.info("Received uploaded document: %s", file.filename)
        if not file.filename:
            raise HTTPException(status_code=400, detail="A file name is required.")

        filename = Path(file.filename).name
        if Path(filename).suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

        ensure_directories()
        destination = Path(settings.data_dir) / filename
        file_bytes = await file.read()
        destination.write_bytes(file_bytes)

        ingestor = DocumentIngestor()
        result = ingestor.ingest([str(destination)])
        return JSONResponse(
            {
                "status": "success",
                "file_name": filename,
                "message": "File uploaded and indexed successfully.",
                "details": result,
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("File upload failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ingest")
def ingest_documents(request: IngestRequest) -> JSONResponse:
    """Load documents, chunk them, embed them, and persist a FAISS index."""
    try:
        logger.info("Starting ingestion pipeline")
        ingestor = DocumentIngestor()
        result = ingestor.ingest(request.file_paths)
        return JSONResponse({"status": "success", "details": result})
    except Exception as exc:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _run_retrieval(cleaned_query: str, top_k: int) -> List[dict]:
    """Execute semantic search and normalize the result payload."""
    retriever = VectorStoreManager()
    documents = retriever.retrieve(cleaned_query, top_k=top_k)
    return [
        {"content": doc.page_content, "metadata": doc.metadata}
        for doc in documents
    ]


def _update_memory(session_id: str, query: str, answer: str) -> None:
    """Keep the recent conversation turns for optional conversational QA."""
    memory = memory_store[session_id]
    memory.extend(
        [
            {"role": "user", "content": query},
            {"role": "assistant", "content": answer},
        ]
    )
    max_turns = settings.max_chat_history * 2
    if len(memory) > max_turns:
        memory_store[session_id] = memory[-max_turns:]


@app.post("/query")
def query_documents(request: QueryRequest) -> JSONResponse:
    """Process a query through preprocessing, retrieval, and answer generation."""
    try:
        logger.info("Received query request")
        processed = preprocess_query(request.query)
        retrieved_docs = _run_retrieval(processed["cleaned_query"], request.top_k)
        llm_service = LLMService()
        chat_history = memory_store.get(request.session_id, [])
        answer = llm_service.generate_answer(
            query=processed["cleaned_query"],
            documents=retrieved_docs,
            chat_history=chat_history,
        )
        _update_memory(request.session_id, request.query, answer)

        retrieval_precision = simple_precision_at_k(
            [doc["content"] for doc in retrieved_docs], processed["tokens"]
        )

        response = {
            "query": processed["original_query"],
            "cleaned_query": processed["cleaned_query"],
            "token_count": processed["token_count"],
            "answer": answer,
            "metrics": {
                "retrieved_chunks": len(retrieved_docs),
                "precision_at_k": round(retrieval_precision, 3),
            },
        }
        if request.include_sources:
            response["sources"] = [doc["metadata"] for doc in retrieved_docs]
        return JSONResponse(response)
    except FileNotFoundError as exc:
        logger.exception("Query attempted before ingestion")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Query processing failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ask")
def ask_question(request: AskRequest) -> JSONResponse:
    """Compatibility endpoint for simple chat UIs that only expect an answer."""
    try:
        logger.info("Received /ask request")
        processed = preprocess_query(request.query)
        retrieved_docs = _run_retrieval(processed["cleaned_query"], settings.top_k)
        llm_service = LLMService()
        chat_history = memory_store.get(request.session_id, [])
        answer = llm_service.generate_answer(
            query=processed["cleaned_query"],
            documents=retrieved_docs,
            chat_history=chat_history,
        )
        _update_memory(request.session_id, request.query, answer)
        return JSONResponse({"answer": answer})
    except FileNotFoundError as exc:
        logger.exception("Ask attempted before ingestion")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Ask processing failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/query/stream")
async def stream_query(request: QueryRequest) -> StreamingResponse:
    """Return a streaming answer while preserving the same retrieval pipeline."""
    try:
        logger.info("Received streaming query request")
        processed = preprocess_query(request.query)
        retrieved_docs = _run_retrieval(processed["cleaned_query"], request.top_k)
        llm_service = LLMService()
        chat_history = memory_store.get(request.session_id, [])

        async def event_generator():
            collected_chunks: List[str] = []
            async for chunk in llm_service.stream_answer(
                query=processed["cleaned_query"],
                documents=retrieved_docs,
                chat_history=chat_history,
            ):
                collected_chunks.append(chunk)
                yield f"data: {json.dumps({'token': chunk})}\n\n"

            answer = "".join(collected_chunks)
            _update_memory(request.session_id, request.query, answer)
            yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except FileNotFoundError as exc:
        logger.exception("Streaming query attempted before ingestion")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Streaming query failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
