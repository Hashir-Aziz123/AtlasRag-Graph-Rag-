import requests
import json

API_URL = "http://localhost:8000/api/v1/query/"

def query_fastapi(question: str):
    """Sends a POST request to the FastAPI query endpoint."""
    print(f"\n[*] Question: '{question}'")
    
    payload = {"query": question}
    
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status() 
        
        data = response.json()
        
        print(f"    -> Intent Routed As: {data.get('routed_intent', 'UNKNOWN')}")
        print("\n[-] Final Answer:")
        print("-" * 50)
        print(data.get('answer', 'No answer provided by API.'))
        print("-" * 50)
        
    except requests.exceptions.RequestException as e:
        print(f"[!] API Request Failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"    Details: {e.response.text}")

def run_tests():
    # Test 1: Should trigger the PRODUCTS template and pull the massive product web
    query_fastapi("What specific GPU architectures and data center products does NVIDIA produce?")
    
    # Test 2: Should trigger the COMPETITORS template
    query_fastapi("Which companies does NVIDIA compete with in the cloud services and computing processor market?")
    
    # Test 3: Should trigger the multi-entity shortestPath graph traversal (Testing the hyphen sanitization)
    query_fastapi("How is Jen-Hsun Huang historically connected to AMD?")
    
    # Test 4: Should trigger Hybrid RAG (Graph + Vector) for a complex geopolitical query
    query_fastapi("What export controls has the USG imposed on China, and which specific NVIDIA products are affected?")
    
    # Test 5: Executive employment history (Testing vector context fallback for non-templated queries)
    query_fastapi("What positions did Colette M. Kress hold before joining NVIDIA?")

if __name__ == "__main__":
    print("Initializing API Client Test...")
    run_tests()