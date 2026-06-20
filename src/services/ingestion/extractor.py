import os
import asyncio
import instructor
from groq import AsyncGroq
from src.models.schemas import GraphExtraction
from config.settings import settings
from dotenv import load_dotenv

load_dotenv()

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
client = instructor.from_groq(groq_client, mode=instructor.Mode.JSON)

async def extract_graph_entities(text_chunk: str) -> GraphExtraction:
    """
    Forces LLaMA-3 to read a text chunk and return strictly typed Graph data.
    """
    system_prompt = """
    You are an expert data extraction pipeline for a Corporate Knowledge Graph.
    Your job is to read SEC 10-K filings, identify core business entities, and map relationships.
    
    STRICT MAPPING RULES:
    1. DEDUPLICATION: Normalize entity names aggressively. "NVIDIA Corp", "NVIDIA", and "NVIDIA CORPORATION" must all map to "NVIDIA".
    2. ACQUISITIONS: If one company buys, acquires, or merges with another, use the `ACQUIRED` relation type. Do NOT use `COMPETES_WITH` for acquisitions.
    3. INFRASTRUCTURE & PRODUCTS: Tools, software suites, or hardware architectures (e.g., Blackboard, Omniverse) must be categorized as `Product` or `Technology`.
    4. RELATION VALIDITY: Ensure relation_type adheres perfectly to the allowed Pydantic literal strings.
    """

    extracted_data = await client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        response_model=GraphExtraction, 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract graph data from this text:\n\n{text_chunk}"}
        ],
        temperature=0.0
    )

    return extracted_data


    from src.services.ingestion.parser import extract_text_from_pdf
    from src.services.ingestion.chunker import chunk_document
    
    async def run_test():
        target_pdf = settings.RAW_DATA_DIR / "sample.pdf"
        full_text = extract_text_from_pdf(str(target_pdf))
        chunks = chunk_document(full_text)
        test_chunk = chunks[10] 
        
        print("Re-running extraction with updated corporate schema...")
        graph_data = await extract_graph_entities(test_chunk)
        
        print("\n[✔] UPDATED AI EXTRACTION COMPLETE:\n")
        print(graph_data.model_dump_json(indent=2))

    asyncio.run(run_test())