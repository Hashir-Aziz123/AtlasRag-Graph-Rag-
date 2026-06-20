import asyncio
import os
from pathlib import Path
import time

from src.workers.workers import celery_app
from src.services.ingestion.parser import extract_text_from_pdf
from src.services.ingestion.chunker import chunk_document
from src.services.ingestion.extractor import extract_graph_entities
from src.services.ingestion.graph_writer import write_to_neo4j
from src.core.embedder import generate_embedding
from src.core.vector_store import init_qdrant_collection, write_to_qdrant

from src.core.vector import qdrant_client
from qdrant_client.models import Filter, FieldCondition, Range

async def async_ingestion_pipeline(file_path: str, start_page: int = 0, end_page: int = None):
    """The core async logic pulled from our integration tests."""
    print(f"[*] Starting background ingestion for: {file_path}")
    
    full_text = extract_text_from_pdf(file_path, start_page=start_page, end_page=end_page)
    chunks = chunk_document(full_text)
    
    await init_qdrant_collection()
    
    semaphore = asyncio.Semaphore(1)
    
    async def process_chunk(idx, chunk):
        async with semaphore:
            try:
                graph_data = await extract_graph_entities(chunk)
                await write_to_neo4j(graph_data)

                vector = generate_embedding(chunk)
                await write_to_qdrant(
                    text_chunk=chunk,
                    vector=vector,
                    chunk_index=idx,
                    document_name=os.path.basename(file_path)
                )
                print(f"      Chunk {idx + 1}/{len(chunks)} processed.")
                await asyncio.sleep(10)
            except Exception as e:
                print(f"      Error on chunk {idx + 1}: {e}")
                await asyncio.sleep(10)

    tasks = [process_chunk(idx, chunk) for idx, chunk in enumerate(chunks)]
    await asyncio.gather(*tasks)
    
    return f"Successfully processed {len(chunks)} chunks from {file_path}."

@celery_app.task(bind=True, name="process_pdf_task")
def process_pdf_task(self, file_path: str, start_page: int = 0, end_page: int = None):
    """
    The synchronous Celery wrapper. 
    This is the function FastAPI will call to queue the job.
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}
        
    try:
        result = asyncio.run(async_ingestion_pipeline(file_path, start_page, end_page))
        return {"status": "success", "message": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

async def async_sweep_vectors():
    """Background task to bulk-delete expired vectors from Qdrant."""
    current_time = int(time.time())
    print(f"[*] Sweeping Qdrant cache for vectors expired before Unix Timestamp: {current_time}")
    
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
        print("      Graveyard successfully purged.")
    except Exception as e:
        print(f"      Failed to sweep Qdrant cache: {e}")

@celery_app.task(name="sweep_orphaned_vectors")
def sweep_orphaned_vectors_task():
    """Synchronous Celery wrapper for the sweeper."""
    asyncio.run(async_sweep_vectors())