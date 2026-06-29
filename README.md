# Enterprise Graph RAG Platform

A production-grade, asynchronous **Hybrid Retrieval-Augmented Generation (RAG)** platform that combines semantic vector search with knowledge graph traversal to provide grounded, explainable responses.

Unlike conventional RAG systems that rely solely on embedding similarity, this architecture separates **semantic retrieval** from **deterministic relationship traversal**, selecting and combining retrieval strategies based on the user's query to improve answer quality and factual grounding.

---

# Architecture

The system is divided into two independent pipelines:

* **Background Ingestion Engine** – Handles document processing, graph extraction, and embedding generation asynchronously.
* **Reactive Retrieval Service** – Executes hybrid search and answer generation with low latency.

---

# Tech Stack

| Component          | Technology                   |
| ------------------ | ---------------------------- |
| Backend            | FastAPI                      |
| Frontend           | Next.js, React, Tailwind CSS |
| Task Queue         | Celery + Redis               |
| Relational Storage | PostgreSQL                   |
| Vector Database    | Qdrant                       |
| Graph Database     | Neo4j                        |
| LLM Provider       | Groq (Llama 3 8B / 70B)      |
| Validation         | Instructor + Pydantic        |
| State Management   | TanStack Query               |

---

# System Architecture

## Storage Layer

The platform maintains eventual consistency across four specialized databases.

### PostgreSQL

The system's source of truth.

Stores:

* Document metadata
* SHA-256 hashes
* Original text chunks
* UUID mappings

Every chunk receives a UUID which is referenced throughout the pipeline.

---

### Redis

Acts as the Celery message broker and result backend.

Responsible for:

* Asynchronous ingestion queues
* Worker communication
* Scheduled task coordination

---

### Qdrant

Stores vector embeddings using a **Pointer Strategy**.

Instead of duplicating document text inside the vector database, Qdrant stores:

* Embeddings
* Metadata
* PostgreSQL UUID references

The original text is retrieved from PostgreSQL when needed, significantly reducing memory usage while keeping the vector index lightweight.

---

### Neo4j

Stores structured knowledge extracted from documents.

Example entity types include:

* Companies
* Products
* People
* Organizations

Relationships preserve document provenance, allowing every retrieved fact to be traced back to its originating source document.

---

## Compute Layer

### FastAPI

Provides asynchronous REST endpoints for:

* Document uploads
* Retrieval
* Query execution
* Task monitoring

---

### Celery Workers

Heavy operations execute outside the request lifecycle, including:

* Document parsing
* Chunk generation
* Embedding creation
* Entity extraction
* Graph construction

A Celery Beat scheduler performs periodic maintenance tasks such as cleanup jobs.

---

### LLM Pipeline

Powered by **Groq** using **Llama 3 (8B & 70B)**.

Structured outputs are enforced using **Instructor** with **Pydantic schemas**, ensuring reliable JSON extraction for:

* Entity recognition
* Relationship extraction
* Query routing

---

### Frontend

Built with:

* Next.js
* React
* Tailwind CSS
* Lucide Icons
* TanStack Query

The interface reacts to backend task progress through asynchronous polling and optimistic UI updates.

---

# Features

## Hybrid Retrieval

Queries combine two complementary retrieval methods:

* Semantic similarity search from Qdrant
* Graph traversal from Neo4j

The retrieval strategy is selected automatically using an LLM-based query router.

Example:

> **"What companies did NVIDIA acquire?"**

→ Graph traversal

> **"Summarize the financial risks discussed in the report."**

→ Vector similarity search

---

## Topological Document Chunking

Instead of fixed-size chunking, documents are parsed structurally.

The chunker:

* Preserves section hierarchy
* Binds headings to paragraphs
* Isolates HTML tables
* Prevents oversized token windows

This improves retrieval quality while maintaining contextual integrity.

---

## Knowledge Graph Extraction

Entities and relationships are extracted from documents into Neo4j, enabling deterministic reasoning over structured information.

Every graph node and relationship maintains provenance back to its originating document.

---

## Cryptographic Deduplication

Documents are hashed using **SHA-256** before ingestion.

Previously processed files are skipped automatically, preventing duplicate:

* Embeddings
* Graph extraction
* Database writes

---

# Getting Started

## Prerequisites

Install the following:

* Python 3.10+
* Node.js 18+
* Docker & Docker Compose
* Groq API Key

---

# Environment Variables

Create a `.env` file in the project root.

```env
# API Keys
GROQ_API_KEY=your_groq_api_key_here

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/graphrag

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=corporate_knowledge

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password
```

---

# Installation

## 1. Start the Database Stack

```bash
cd docker
docker-compose up -d
```

This launches:

* PostgreSQL
* Redis
* Qdrant
* Neo4j

---

## 2. Start the Backend

Create and activate a virtual environment.

```bash
python -m venv venv
```

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Run the FastAPI server.

```bash
uvicorn src.api.v1.main:app --reload --port 8000
```

---

## 3. Start Celery

Run the worker and scheduler in separate terminals.

### Worker

**Linux / macOS**

```bash
celery -A src.workers.workers.celery_app worker --loglevel=info
```

**Windows**

```bash
celery -A src.workers.workers.celery_app worker --pool=solo --loglevel=info
```

### Beat Scheduler

```bash
celery -A src.workers.workers.celery_app beat --loglevel=info
```

---

## 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The application will be available at:

```text
http://localhost:3000
```

---

# Windows Quick Start

A convenience script is included for Windows users.

```bash
startup.bat
```

The script automatically launches:

* FastAPI
* Celery Worker
* Celery Beat

each in its own terminal window.

---

# Project Highlights

* Hybrid Graph + Vector Retrieval
* Asynchronous document ingestion
* Structural document chunking
* Knowledge graph extraction
* Deterministic relationship traversal
* Cryptographic document deduplication
* Provenance-aware retrieval
* Production-oriented multi-database architecture
