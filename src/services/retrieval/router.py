import os
import instructor
from groq import AsyncGroq
from dotenv import load_dotenv

from src.models.schemas import ParsedQuery

load_dotenv()

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
client = instructor.from_groq(groq_client, mode=instructor.Mode.JSON)

async def route_user_query(query: str) -> ParsedQuery:
    """
    Analyzes a natural language question and extracts the intent and targets.
    Uses a faster, lighter LLM specifically for rapid NLP routing.
    """
    system_prompt = """
    You are a query routing engine for a corporate knowledge base.
    Read the user's question and determine their intent.
    
    ROUTING RULES:
    - If they ask about buyouts, mergers, or acquisitions -> 'acquisitions'
    - If they ask about software, hardware, or ecosystems -> 'products'
    - If they ask about market rivals or market share -> 'competitors'
    - If they ask a fuzzy, conceptual, or strategy-based question -> 'general'
    
    Extract the exact names of any entities mentioned to populate the database query template.
    """

    parsed_result = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        response_model=ParsedQuery,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.0
    )

    return parsed_result
