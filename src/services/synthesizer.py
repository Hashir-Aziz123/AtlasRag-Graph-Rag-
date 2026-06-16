import os
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

async def generate_response(original_query: str, context: str) -> str:
    """
    Takes the raw database context and the user's question, 
    and synthesizes a final, human-readable answer.
    """
    system_prompt = """
    You are an expert corporate intelligence analyst.
    Answer the user's question using ONLY the provided database context.
    
    RULES:
    1. If the context contains the answer, synthesize it into a clear, professional response.
    2. If the context does not contain the answer, explicitly state that you do not have enough information.
    3. DO NOT hallucinate or draw on outside knowledge. You are strictly bounded by the context.
    """

    user_prompt = f"DATABASE CONTEXT:\n{context}\n\nUSER QUESTION: {original_query}"

    response = await groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        # Low temperature forces the model to be factual and stick to the context
        temperature=0.2 
    )

    return response.choices[0].message.content