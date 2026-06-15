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
        except Exception as e:
            print(f"\n[⚠️] Failed to process chunk {idx + 1}: {e}")

async def run():
    file_name = "sample.pdf"
    target_pdf = settings.RAW_DATA_DIR / file_name
    
    if not target_pdf.exists():
        print(f"[❌] Source file not found: {target_pdf}")
        return

    print(f"[*] Starting Dual-Path Ingestion Test for: {file_name}")
    
    print("[1/4] Extracting text...")
    full_text = extract_text_from_pdf(str(target_pdf))
    
    print("[2/4] Chunking document...")
    all_chunks = chunk_document(full_text)
    
    chunks = all_chunks[:10]
    total_chunks = len(chunks)
    print(f"      Total generated: {len(all_chunks)} chunks. Capping execution to the first {total_chunks} chunks.")

    print("[3/4] Ensuring database collections are initialized...")
    # No arguments needed! It uses the singleton internally.
    await init_qdrant_collection()

    print("[4/4] Processing chunks concurrently (Max concurrency: 3)...")
    semaphore = asyncio.Semaphore(3)
    
    # We only pass the 4 arguments the function actually expects
    tasks = [
        process_chunk_dual_path(idx, chunk, file_name, semaphore)
        for idx, chunk in enumerate(chunks)
    ]
    
    await asyncio.gather(*tasks)
    print(f"\n[✔] Dual-path validation complete. Check both your database instances.")

if __name__ == "__main__":
    asyncio.run(run())