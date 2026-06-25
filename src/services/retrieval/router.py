import instructor
from groq import AsyncGroq

from config.settings import settings
from src.models.schemas import ParsedQuery

# Enforce fail-fast initialization via central settings
groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
client = instructor.from_groq(groq_client, mode=instructor.Mode.JSON)

async def route_user_query(query: str) -> ParsedQuery:
    """
    Analyzes a natural language question and extracts the intent, entities, 
    and any temporal or document-specific constraints.
    """
    system_prompt = """
    You are a highly precise query routing engine for a corporate knowledge base.
    Analyze the user's question and extract the routing parameters.
    
    ROUTING RULES:
    - Buyouts, mergers, or acquisitions -> 'acquisitions'
    - Software, hardware, or ecosystems -> 'products'
    - Market rivals or market share -> 'competitors'
    - Fuzzy, conceptual, or strategy-based questions -> 'general'
    
    EXTRACTION RULES:
    1. Extract exact canonical names of entities (e.g., "NVIDIA", "Microsoft").
    2. If the user restricts their query to a specific report, year, or filing (e.g., "2023 10-K", "Q3 earnings"), extract it exactly into 'target_document'. Do not invent a document if one is not mentioned.
    """

    parsed_result = await client.chat.completions.create(
        model=settings.GROQ_MODEL_NAME,  # Using the 8B model for rapid classification
        response_model=ParsedQuery,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.0
    )

    return parsed_result