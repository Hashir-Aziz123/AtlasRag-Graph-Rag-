from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.routers import ingestion, retrieval

app = FastAPI(
    title="Hybrid GraphRAG Engine",
    description="Dual-path MLOps pipeline for structured and semantic corporate intelligence.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router, prefix="/api/v1/ingest", tags=["Ingestion"])
app.include_router(retrieval.router, prefix="/api/v1/query", tags=["Retrieval"])

@app.get("/health", tags=["System"])
async def health_check():
    """Liveness probe for infrastructure monitoring."""
    return {"status": "healthy", "service": "graphrag-api"}