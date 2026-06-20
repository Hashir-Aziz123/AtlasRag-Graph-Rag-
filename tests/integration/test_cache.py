import time
import requests

API_URL = "http://localhost:8000/api/v1/query/"

def test_cache_performance():
    print("Initializing Semantic Cache Test Protocol...\n")
    
    # This should trigger a Cache Miss, hit Neo4j/Qdrant, and take ~3-5 seconds.
    query_1 = "What specific GPU architectures and data center products does NVIDIA produce?"
    print(f"[*] Sending Request 1 (Expect Cache Miss):")
    print(f"    -> '{query_1}'")
    
    start_time = time.perf_counter()
    response = requests.post(API_URL, json={"query": query_1})
    end_time = time.perf_counter()
    
    data = response.json()
    print(f"    [✔] Intent Routed As: {data.get('routed_intent', 'UNKNOWN')}")
    print(f"    [⏱] Response Time: {end_time - start_time:.4f} seconds.")
    
    print("-" * 65)

    # This should hit the Qdrant cache and bypass the pipeline entirely.
    print(f"[*] Sending Request 2 (Expect Exact Cache Hit):")
    print(f"    -> '{query_1}'")
    
    start_time = time.perf_counter()
    response = requests.post(API_URL, json={"query": query_1})
    end_time = time.perf_counter()
    
    data = response.json()
    print(f"    [✔] Intent Routed As: {data.get('routed_intent', 'UNKNOWN')}")
    print(f"    [⏱] Response Time: {end_time - start_time:.4f} seconds.")

    print("-" * 65)

    # The wording is entirely different, but the mathematical meaning is the same.
    query_2 = "Can you list the data center products and GPU architectures produced by NVIDIA?"
    print(f"[*] Sending Request 3 (Expect Semantic Vector Hit):")
    print(f"    -> '{query_2}'")
    
    start_time = time.perf_counter()
    response = requests.post(API_URL, json={"query": query_2})
    end_time = time.perf_counter()
    
    data = response.json()
    print(f"    [✔] Intent Routed As: {data.get('routed_intent', 'UNKNOWN')}")
    print(f"    [⏱] Response Time: {end_time - start_time:.4f} seconds.")

if __name__ == "__main__":
    test_cache_performance()