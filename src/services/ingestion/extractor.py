import instructor
from groq import AsyncGroq

from config.settings import settings
from src.models.schemas import GraphExtraction

groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
client = instructor.from_groq(groq_client, mode=instructor.Mode.JSON)

async def extract_graph_entities(text_chunk: str) -> GraphExtraction:
    """
    Forces the configured LLM to read a text chunk and return strictly typed Graph data.
    """
    system_prompt = """
    You are an expert data extraction pipeline for a Corporate Knowledge Graph.
    Your job is to read SEC filings and corporate documents, identify core business entities, and map relationships.
    
    STRICT MAPPING RULES:
    1. DEDUPLICATION: Normalize entity names aggressively. "NVIDIA Corp", "NVIDIA", and "NVIDIA CORPORATION" must all map to "NVIDIA".
    2. ACQUISITIONS: If one company buys, acquires, or merges with another, use the `ACQUIRED` relation type. Do NOT use `COMPETES_WITH` for acquisitions.
    3. INFRASTRUCTURE & PRODUCTS: Tools, software suites, or hardware architectures (e.g., Blackboard, Omniverse) must be categorized as `Product` or `Technology`.
    4. RELATION VALIDITY: Ensure relation_type adheres perfectly to the allowed Pydantic literal strings.
    """

    extracted_data = await client.chat.completions.create(
        model=settings.GROQ_MODEL_NAME, 
        response_model=GraphExtraction, 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract graph data from this text:\n\n{text_chunk}"}
        ],
        temperature=0.0
    )

    return extracted_data