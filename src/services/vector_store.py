from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

from config.settings import settings
from src.core.vector import qdrant_client

async def init_qdrant_collection():
    """Checks if the collection exists, and creates it if it doesn't."""
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

async def write_to_qdrant(text_chunk: str, vector: list[float], chunk_index: int, document_name: str):
    """
    Takes a pre-computed vector and pushes it to Qdrant 
    along with the raw text as the metadata payload.
    """
    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_name}_chunk_{chunk_index}"))
    
    point = PointStruct(
        id=point_id,
        vector=vector,
        payload={
            "document": document_name,
            "chunk_index": chunk_index,
            "text": text_chunk
        }
    )
    
    await qdrant_client.upsert(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points=[point]
    )