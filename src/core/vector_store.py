from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import Dict, Any

from config.settings import settings
from src.core.vector import qdrant_client

async def init_qdrant_collection():
    collections_response = await qdrant_client.get_collections()
    existing_collections = [c.name for c in collections_response.collections]
    
    if settings.QDRANT_COLLECTION_NAME not in existing_collections:
        print(f"[*] Creating new Qdrant collection: {settings.QDRANT_COLLECTION_NAME}")
        await qdrant_client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIMENSION, 
                distance=Distance.COSINE
            ),
        )

async def write_to_qdrant(chunk_id: str, vector: list[float], metadata: Dict[str, Any]):
    """
    Pushes a vector to Qdrant utilizing the Pointer Strategy.
    The point ID matches the PostgreSQL Chunk UUID exactly, allowing fast O(1) text retrieval.
    Raw text is explicitly omitted from the payload to conserve RAM.
    """
    payload = {
        **metadata
    }
    
    point = PointStruct(
        id=chunk_id,  # Directly map to PostgreSQL UUID
        vector=vector,
        payload=payload
    )
    
    await qdrant_client.upsert(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points=[point]
    )