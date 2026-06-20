import hashlib
import asyncio
import uuid
import time
from typing import Optional
import redis.asyncio as aioredis
from qdrant_client.models import Distance, VectorParams, PointStruct

from config.settings import settings
from src.core.vector import qdrant_client
from src.services.embedder import generate_embedding

redis_session = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

CACHE_COLLECTION = "semantic_cache"
CACHE_THRESHOLD = 0.95
CACHE_TTL = 86400  

async def init_cache_index():
    collections = await qdrant_client.get_collections()
    existing_collections = [c.name for c in collections.collections]
    if CACHE_COLLECTION not in existing_collections:
        await qdrant_client.create_collection(
            collection_name=CACHE_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

def generate_query_hash(query: str) -> str:
    return hashlib.sha256(query.strip().lower().encode()).hexdigest()

def generate_deterministic_uuid(query_hash: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_OID, query_hash))

async def get_cached_response(query: str) -> Optional[str]:
    query_vector = await asyncio.to_thread(generate_embedding, query)
    
    search_results = await qdrant_client.search(
        collection_name=CACHE_COLLECTION,
        query_vector=query_vector,
        limit=1
    )
    
    if not search_results or search_results[0].score < CACHE_THRESHOLD:
        return None
        
    query_hash = search_results[0].payload.get("query_hash")
    if not query_hash:
        return None
        
    cached_text = await redis_session.get(f"cache:{query_hash}")
    
    if not cached_text:
        # Asynchronous Read-Repair: Fire and forget the deletion so we don't block the hot path
        orphaned_point_id = generate_deterministic_uuid(query_hash)
        asyncio.create_task(qdrant_client.delete(
            collection_name=CACHE_COLLECTION,
            points_selector=[orphaned_point_id]
        ))
        return None
        
    return cached_text

async def set_cached_response(query: str, answer: str):
    query_hash = generate_query_hash(query)
    point_id = generate_deterministic_uuid(query_hash)
    query_vector = await asyncio.to_thread(generate_embedding, query)
    
    # Calculate the exact expiration time
    expires_at = int(time.time()) + CACHE_TTL
    
    await redis_session.setex(f"cache:{query_hash}", CACHE_TTL, answer)
    
    await qdrant_client.upsert(
        collection_name=CACHE_COLLECTION,
        points=[
            PointStruct(
                id=point_id,
                vector=query_vector,
                payload={
                    "query_hash": query_hash, 
                    "raw_query": query,
                    "expires_at": expires_at  # Injected metadata for the sweeper
                }
            )
        ]
    )