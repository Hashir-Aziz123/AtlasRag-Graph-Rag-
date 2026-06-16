import asyncio
from dotenv import load_dotenv

from config.settings import settings
from src.services.parser import extract_text_from_pdf
from src.services.chunker import chunk_document
from src.services.extractor import extract_graph_entities
from src.services.generator import write_to_neo4j
from src.services.embedder import generate_embedding
from src.services.vector_store import init_qdrant_collection, write_to_qdrant

load_dotenv()

async def process_chunk_dual_path(idx, chunk, file_name, semaphore):
    async with semaphore:
        try:
            # Path A: Knowledge Graph
            graph_data = await extract_graph_entities(chunk)
            await write_to_neo4j(graph_data)

            # Path B: Vector Semantics
            vector = generate_embedding(chunk)
            await write_to_qdrant(
                text_chunk=chunk,
                vector=vector,
                chunk_index=idx,
                document_name=file_name
            )
            print(f"      [✔] Chunk {idx + 1} processed successfully.")
            await asyncio.sleep(10)


        except Exception as e:
            print(f"\n[⚠️] Failed to process chunk {idx + 1}: {e}")
            await asyncio.sleep(10)

async def run():
    file_name = "sample.pdf"
    target_pdf = settings.RAW_DATA_DIR / file_name
    
    if not target_pdf.exists():
        print(f"[❌] Source file not found: {target_pdf}")
        return

    print(f"[*] Starting Dual-Path Ingestion Test for: {file_name}")
    
    # Step 1: Parse a specific 8-page slice (Pages 4 through 11, 0-indexed)
    print("[1/4] Extracting text (Pages 4 through 12)...")
    full_text = extract_text_from_pdf(str(target_pdf), start_page=4, end_page=12)
    
    # Step 2: Chunk the specific slice
    print("[2/4] Chunking document...")
    chunks = chunk_document(full_text)
    total_chunks = len(chunks)
    print(f"      Total generated: {total_chunks} chunks.")

    # Step 3: Initialize Storage Schemas
    print("[3/4] Ensuring database collections are initialized...")
    await init_qdrant_collection()

    # Step 4: Dispatch Concurrent Workers
    print("[4/4] Processing chunks concurrently (Max concurrency: 3)...")
    semaphore = asyncio.Semaphore(1)
    
    tasks = [
        process_chunk_dual_path(idx, chunk, file_name, semaphore)
        for idx, chunk in enumerate(chunks)
    ]
    
    # Execute all tasks concurrently
    await asyncio.gather(*tasks)
    print(f"\n[✔] Dual-path validation complete. Check both your database instances.")

if __name__ == "__main__":
    asyncio.run(run())