import asyncio
import time
import requests

from qdrant_client.models import Filter, FieldCondition, Range
from src.services.cache_manager import (
    generate_query_hash,
    generate_deterministic_uuid,
    redis_session,
    CACHE_COLLECTION
)
from src.core.vector import qdrant_client

API_URL = "http://localhost:8000/api/v1/query/"

async def run_lifecycle_test():
    print("Initializing Time-Accelerated Cache Lifecycle Test...\n")

    query_1 = "What is the core mechanism of the Transformer architecture?"
    hash_1 = generate_query_hash(query_1)
    redis_key_1 = f"cache:{hash_1}"

    # --- PHASE 1: The Baseline ---
    print("[*] Phase 1: Warming up the cache (Expect ~3-5s)...")
    start = time.perf_counter()
    resp = requests.post(API_URL, json={"query": query_1})
    print(f"    -> Intent: {resp.json().get('routed_intent')}")
    print(f"    -> Latency: {time.perf_counter() - start:.2f}s")

    print("\n[*] Phase 2: Verifying standard cache hit (Expect < 0.05s)...")
    start = time.perf_counter()
    resp = requests.post(API_URL, json={"query": query_1})
    print(f"    -> Intent: {resp.json().get('routed_intent')}")
    print(f"    -> Latency: {time.perf_counter() - start:.4f}s")

    # --- PHASE 3: Read-Repair (Lazy Deletion) ---
    print("\n[*] Phase 3: Simulating 24-hour TTL expiration for Read-Repair...")
    print("    -> Erasing Redis payload to simulate expiration...")
    await redis_session.delete(redis_key_1)

    print("    -> Sending identical query (Expect full latency as cache self-heals)...")
    start = time.perf_counter()
    resp = requests.post(API_URL, json={"query": query_1})
    print(f"    -> Intent: {resp.json().get('routed_intent')}")
    print(f"    -> Latency: {time.perf_counter() - start:.2f}s")

    # --- PHASE 4: The Sweeper (Active Deletion) ---
    print("\n[*] Phase 4: Testing the Background Sweeper Logic...")
    query_2 = "What is an entirely unique one-off question about NVIDIA?"
    hash_2 = generate_query_hash(query_2)
    point_id_2 = generate_deterministic_uuid(hash_2)

    print("    -> Injecting unique query into the cache...")
    requests.post(API_URL, json={"query": query_2})

    print("    -> Artificially aging the Qdrant vector by 48 hours...")
    past_timestamp = int(time.time()) - 172800  # 48 hours ago
    await qdrant_client.set_payload(
        collection_name=CACHE_COLLECTION,
        payload={"expires_at": past_timestamp},
        points=[point_id_2]
    )

    print("    -> Manually executing the graveyard sweep...")
    await qdrant_client.delete(
        collection_name=CACHE_COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="expires_at",
                    range=Range(lt=int(time.time()))
                )
            ]
        )
    )

    print("    -> Verifying Qdrant graveyard is empty...")
    points = await qdrant_client.retrieve(collection_name=CACHE_COLLECTION, ids=[point_id_2])

    if not points:
        print("    SUCCESS: The sweeper successfully assassinated the expired vector.")
    else:
        print("    FAILURE: The vector survived the sweep.")

    await redis_session.aclose()

if __name__ == "__main__":
    asyncio.run(run_lifecycle_test())