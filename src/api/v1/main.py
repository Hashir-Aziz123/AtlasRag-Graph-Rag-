from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.routers import ingestion, retrieval
from src.services.cache_manager import init_cache_index

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event manager for global API startup and shutdown routines."""
    await init_cache_index()
    yield


app = FastAPI(
    title="Hybrid GraphRAG Engine",
    description="Dual-path MLOps pipeline for structured and semantic corporate intelligence.",
    version="1.0.0",
    lifespan=lifespan
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
    return {"status": "healthy", "service": "graphrag-api"}