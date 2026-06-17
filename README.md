# Hybrid GraphRAG Engine

A GraphRAG system for extracting, storing, and querying corporate knowledge from unstructured documents.

The platform combines graph-based retrieval through Neo4j with semantic vector search through Qdrant, enabling both relationship-aware reasoning and contextual document retrieval. Rather than relying solely on vector similarity, the system leverages explicit entity relationships to answer questions involving organizational structures, dependencies, and interconnected business information.

> **Project Status:** Active Development
> Core ingestion and hybrid retrieval systems are implemented. Distributed task processing, API exposure, and caching layers are currently being integrated.

---

## Architecture

### Ingestion Pipeline

Documents are processed through a multi-stage extraction pipeline:

```text
PDF Documents
      │
      ▼
 Text Extraction
      │
      ▼
 Document Chunking
      │
      ▼
 Entity & Relationship Extraction
      │
 ┌────┴────┐
 ▼         ▼
Neo4j    Qdrant
(Graph)  (Vectors)
```

#### Components

* PDF parsing using PyMuPDF (`fitz`)
* Chunk generation for downstream processing
* Structured entity and relationship extraction
* Pydantic schema validation
* Concurrent storage into Neo4j and Qdrant

---

### Retrieval Pipeline

Incoming questions are first classified to determine retrieval strategy.

```text
User Query
     │
     ▼
Intent Router
     │
 ┌───┴────┐
 ▼        ▼
Neo4j   Qdrant
Graph   Vector Search
Search
 └───┬────┘
     ▼
Context Fusion
     ▼
LLM Synthesis
     ▼
Response
```

#### Retrieval Features

* Intent-aware query routing
* Neo4j full-text search indexes
* Relationship traversal and graph exploration
* Dense semantic retrieval through Qdrant
* Concurrent retrieval execution
* Hybrid context fusion
* Context-bounded answer generation

---

## Project Structure

```text
graph-rag-platform/
├── config/
│   └── settings.py

├── src/
│   ├── models/
│   │   └── schemas.py

│   ├── services/
│   │   ├── parser.py
│   │   ├── chunker.py
│   │   ├── extractor.py
│   │   ├── router.py
│   │   ├── fetcher.py
│   │   └── embedder.py
│   │   └── generator.py
│   │   └── synthesizer.py
│   │   └── vector_store.py

│   ├── api/                 # Planned
│   └── tasks/               # Planned

└── tests/
    └── integration/
```

---

## Current Progress

### Completed

* Dockerized Neo4j and Qdrant infrastructure
* Pydantic schemas for nodes and relationships
* PDF ingestion workflow
* Entity and relationship extraction pipeline
* Concurrent graph and vector storage
* Neo4j full-text indexing
* Hybrid retrieval orchestration
* Context fusion layer

### In Progress

* Redis-backed task queue
* Celery worker integration
* Background ingestion processing

### Planned

* FastAPI service layer
* Multi-tenant API endpoints
* Retrieval caching
* Query analytics
* Monitoring and observability stack

---

## Technology Stack

| Layer               | Technology        |
| ------------------- | ----------------- |
| Language            | Python            |
| Graph Database      | Neo4j             |
| Vector Database     | Qdrant            |
| Validation          | Pydantic          |
| Document Processing | PyMuPDF           |
| Task Queue          | Celery (WIP)      |
| Cache Layer         | Redis (WIP)       |
| API Layer           | FastAPI (Planned) |
| Containers          | Docker            |

---
