# LLM-Based Question Answering System

A complete Retrieval-Augmented Generation (RAG) question answering system built with Python, FastAPI, React, Vite, Tailwind CSS, LangChain, FAISS, SentenceTransformers, and the Groq API.

## Features

- FastAPI backend with modular pipeline
- React + Vite frontend with Tailwind CSS
- Document ingestion for PDF, TXT, and DOCX files
- Text cleaning, tokenization, and chunking
- Semantic retrieval with FAISS vector search
- LLM-powered answer generation using Groq
- Source references in responses
- Logging across each pipeline stage
- Optional chat history memory
- Optional streaming responses with Server-Sent Events
- Basic retrieval evaluation metric (`precision_at_k`)
- Drag-and-drop PDF upload UI
- Chat-style Q&A interface with loading and error states
- Optional Streamlit frontend

## Project Structure

```text
.
├── app
│   ├── __init__.py
│   ├── ingestion.py
│   ├── llm.py
│   ├── main.py
│   ├── retriever.py
│   └── utils.py
├── data
├── frontend.py
├── src
│   ├── components
│   │   ├── Chat.jsx
│   │   └── Upload.jsx
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
├── vectorstore
├── .env.example
├── README.md
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── vite.config.js
└── requirements.txt
```

## Pipeline

1. User submits a query through the API.
2. The system cleans and tokenizes the query.
3. The query is semantically matched against ingested document chunks.
4. Top-k relevant chunks are retrieved from FAISS.
5. Retrieved context and the query are sent to the LLM.
6. A grounded answer is returned, optionally with sources and metrics.

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Update `.env` with your `GROQ_API_KEY`.

### 4. Add documents

Place `.pdf`, `.txt`, or `.docx` files in the `data/` directory.

### 5. Start the FastAPI server

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

### 6. Optional: run the Streamlit frontend

```bash
streamlit run frontend.py
```

The UI will be available at `http://127.0.0.1:8501`.

### 7. Run the React frontend

Install frontend dependencies:

```bash
npm install
```

Start the Vite dev server:

```bash
npm run dev
```

The React app will be available at `http://127.0.0.1:5173`.

## API Endpoints

### `GET /health`

Returns API health and version metadata.

### `POST /ingest`

Loads documents, chunks them, generates embeddings, and writes the FAISS index to `vectorstore/`.

Request body:

```json
{
  "file_paths": ["data/sample.txt"]
}
```

You can also pass `null` or omit `file_paths` to scan the full `data/` directory.

### `POST /upload`

Accepts a PDF file via multipart form data, saves it into `data/`, and ingests it immediately.

Example:

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -F "file=@data/example.pdf"
```

### `POST /query`

Processes a question through preprocessing, semantic retrieval, and LLM response generation.

Request body:

```json
{
  "query": "What are the main topics discussed in the documents?",
  "top_k": 4,
  "session_id": "demo-session",
  "include_sources": true
}
```

Example response:

```json
{
  "query": "What are the main topics discussed in the documents?",
  "cleaned_query": "What are the main topics discussed in the documents?",
  "token_count": 9,
  "answer": "The documents primarily discuss ...",
  "metrics": {
    "retrieved_chunks": 4,
    "precision_at_k": 0.75
  },
  "sources": [
    {
      "source": "/absolute/path/to/data/sample.txt",
      "chunk_id": 0
    }
  ]
}
```

### `POST /ask`

Lightweight chat endpoint used by the React frontend.

Request body:

```json
{
  "query": "What does the uploaded PDF say about RAG?"
}
```

Response:

```json
{
  "answer": "The document explains that retrieval-augmented generation combines vector search with an LLM..."
}
```

### `POST /query/stream`

Streams answer tokens back as Server-Sent Events.

Request body is the same as `POST /query`.

Example streaming event:

```text
data: {"token":"The"}

data: {"token":" answer"}

data: {"done":true}
```

## Example cURL Requests

### Ingest documents

```bash
curl -X POST "http://127.0.0.1:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"file_paths":["data/sample.txt"]}'
```

### Query the system

```bash
curl -X POST "http://127.0.0.1:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query":"Summarize the key ideas in the ingested documents.",
    "top_k":4,
    "session_id":"demo-session",
    "include_sources":true
  }'
```

### Ask via frontend-friendly endpoint

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query":"Summarize the uploaded PDF."}'
```

## React Frontend Overview

- `src/components/Upload.jsx`: drag-and-drop PDF picker with multipart upload to `/upload`
- `src/components/Chat.jsx`: chat interface that sends queries to `/ask`
- `src/App.jsx`: responsive two-panel layout and upload status
- `src/index.css`: Tailwind entrypoint and global theme styles

The Vite dev server proxies `/upload`, `/ask`, and `/health` to the FastAPI backend by default.

## Notes

- The default vector database is FAISS for local persistence and simplicity.
- The default embedding model is `sentence-transformers/all-MiniLM-L6-v2`.
- The default LLM provider implementation is Groq via its OpenAI-compatible API endpoint.
- `GROQ_BASE_URL` defaults to `https://api.groq.com/openai/v1`.
- `CORS_ORIGINS` is preconfigured for the Vite development server.
- If you want to support another LLM provider, extend `app/llm.py` with a new provider branch.

## Production Considerations

- Move chat memory from in-process storage to Redis or a database for multi-instance deployments.
- Add authentication and rate limiting for public deployments.
- Add background jobs for large ingestion workloads.
- Add automated tests for ingestion and retrieval behavior.
# LLM-QnA
