# LLM-Based Q&A System (RAG)

A lightweight Retrieval-Augmented Generation (RAG) app using FastAPI + React.

## What it does

- Upload documents (PDF, TXT, DOCX)
- Convert them into embeddings
- Store in FAISS
- Retrieve relevant chunks
- Generate answers using an LLM (Groq)

## Tech Stack

- Backend: FastAPI, LangChain, FAISS
- Frontend: React (Vite + Tailwind)
- Embeddings: SentenceTransformers
- LLM: Groq API

## Core Flow

1. Upload document
2. Chunk + embed
3. Store in FAISS
4. Query -> retrieve top-k chunks
5. LLM generates answer with sources

## Features

- Semantic search
- Chat-style Q&A UI
- PDF upload (drag & drop)
- Source citations
