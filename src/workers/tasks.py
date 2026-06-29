import asyncio
import os
import time
import logging
from pathlib import Path

import groq
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from src.workers.workers import celery_app
from src.services.ingestion.parser import parse_pdf
from src.services.ingestion.chunker import StructuredChunker
from src.services.ingestion.extractor import extract_graph_entities
from src.services.ingestion.graph_writer import write_to_neo4j
from src.services.ingestion.sql_writer import check_document_exists, write_chunks_to_sql
from src.core.embedder import generate_embedding
from src.core.vector_store import init_qdrant_collection, write_to_qdrant
from src.core.vector import qdrant_client
from src.core.graph import init_neo4j_schema
from qdrant_client.models import Filter, FieldCondition, Range

logger = logging.getLogger(__name__)

# --- THE ASYNC FIX ---
# We must maintain a persistent event loop for the Celery worker process.
# Calling asyncio.run() creates and destroys a loop every time. This orphans the 
# underlying asyncio tasks that global DB connection pools (SQLAlchemy, Neo4j, Qdrant) 
# rely on, leading to the dreaded "'NoneType' object has no attribute 'send'" greenlet crash.
_worker_loop = None

def get_worker_loop():
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop

@retry(
    wait=wait_exponential(multiplier=2, min=10, max=300),
    stop=stop_after_attempt(7),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def process_chunk_with_retry(chunk_data: dict, semaphore: asyncio.Semaphore):
    """
    Encapsulates the AI extraction and dual-database writes.
    Because MERGE and upsert are idempotent, retrying this entire block upon failure
    guarantees eventual consistency without duplicating nodes or vectors.
    """
    async with semaphore:
        chunk_id = chunk_data["chunk_id"]
        text_payload = chunk_data["text"]
        metadata_payload = chunk_data["metadata"]

        # 1. Graph Extraction & Persistence
        graph_data = await extract_graph_entities(text_payload)
        await write_to_neo4j(graph_data, metadata_payload)

        # 2. Vector Embedding & Persistence
        vector = generate_embedding(text_payload)
        await write_to_qdrant(
            chunk_id=chunk_id,
            vector=vector,
            metadata=metadata_payload
        )

        # Standard cooldown between successful chunks to ease base API load
        await asyncio.sleep(5)

async def async_ingestion_pipeline(file_path: str):
    """Executes the asynchronous ingestion, chunking, extraction, and storage pipeline."""
    logger.info(f"[*] Starting background ingestion for: {file_path}")
    
    if await check_document_exists(file_path):
        logger.info(f"[*] Aborting: Document '{os.path.basename(file_path)}' has already been ingested.")
        return f"Skipped: {os.path.basename(file_path)} already exists."

    raw_elements = parse_pdf(file_path)
    
    chunker = StructuredChunker(max_tokens=400, overlap_tokens=50)
    parsed_chunks = chunker.chunk_elements(raw_elements)
    
    sql_chunks = await write_chunks_to_sql(file_path, parsed_chunks)
    
    # Initialize Databases before concurrent writes
    await init_qdrant_collection()
    await init_neo4j_schema()
    
    # Throttle concurrency. If using Groq free tier, this MUST be 1.
    semaphore = asyncio.Semaphore(1)
    
    async def task_wrapper(idx: int, chunk: dict):
        try:
            await process_chunk_with_retry(chunk, semaphore)
            logger.info(f"      Chunk {idx + 1}/{len(sql_chunks)} processed successfully.")
        except Exception as e:
            # If it fails after 7 exponential backoff attempts, log the permanent failure.
            # At this point, the chunk exists in PostgreSQL but lacks Graph/Vector representation.
            logger.error(f"      [!] Permanent failure on chunk {idx + 1} after retries: {e}")

    tasks = [task_wrapper(idx, chunk) for idx, chunk in enumerate(sql_chunks)]
    await asyncio.gather(*tasks)
    
    return f"Successfully processed {len(sql_chunks)} chunks from {file_path}."

@celery_app.task(bind=True, name="process_pdf_task")
def process_pdf_task(self, file_path: str):
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}
        
    try:
        # Utilize the persistent loop instead of asyncio.run()
        loop = get_worker_loop()
        result = loop.run_until_complete(async_ingestion_pipeline(file_path))
        return {"status": "success", "message": result}
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

async def async_sweep_vectors():
    current_time = int(time.time())
    logger.info(f"[*] Sweeping Qdrant cache for vectors expired before Unix Timestamp: {current_time}")
    
    try:
        await qdrant_client.delete(
            collection_name="semantic_cache",
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="expires_at",
                        range=Range(lt=current_time) 
                    )
                ]
            )
        )
        logger.info("      Graveyard successfully purged.")
    except Exception as e:
        logger.error(f"      [!] Failed to sweep Qdrant cache: {e}")

@celery_app.task(name="sweep_orphaned_vectors")
def sweep_orphaned_vectors_task():
    try:
        # Apply the persistent loop here as well
        loop = get_worker_loop()
        loop.run_until_complete(async_sweep_vectors())
    except Exception as e:
        logger.error(f"Vector sweep failed: {e}", exc_info=True)