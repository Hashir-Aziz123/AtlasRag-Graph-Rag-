import asyncio
from src.services.router import route_user_query
from src.services.fetcher import fetch_context
from src.services.synthesizer import generate_response

async def ask_graphrag(user_query: str):
    print(f"\n[*] Question: '{user_query}'")
    
    # Step 1: Route the intent
    print("    -> Routing query...")
    parsed_query = await route_user_query(user_query)
    print(f"       Intent: {parsed_query.intent.value} | Entities: {parsed_query.entities}")
    
    # Step 2: Fetch the context
    print("    -> Fetching context (Hybrid RAG)...")
    raw_context = await fetch_context(parsed_query, user_query)
    
    if raw_context == "No relevant information found in the databases.":
        print("\n[!] Answer: No data found in the current ingestion slice.")
        return
        
    # Step 3: Synthesize the final answer
    print("    -> Synthesizing answer...")
    final_answer = await generate_response(user_query, raw_context)
    
    print("\n[-] Final Answer:")
    print("-" * 50)
    print(final_answer)
    print("-" * 50)

async def run_tests():
    # Test 1: Should trigger the PRODUCTS template and pull the massive product web
    await ask_graphrag("What specific GPU architectures and data center products does NVIDIA produce?")
    
    # Test 2: Should trigger the COMPETITORS template
    await ask_graphrag("Which companies does NVIDIA compete with in the cloud services and computing processor market?")
    
    # Test 3: Should trigger the multi-entity shortestPath graph traversal
    await ask_graphrag("How is Jen-Hsun Huang historically connected to AMD?")
    
    # Test 4: Should trigger Hybrid RAG (Graph + Vector) for a complex geopolitical query
    await ask_graphrag("What export controls has the USG imposed on China, and which specific NVIDIA products are affected?")
    
    # Test 5: Executive employment history (Testing vector context fallback for non-templated queries)
    await ask_graphrag("What positions did Colette M. Kress hold before joining NVIDIA?")

if __name__ == "__main__":
    asyncio.run(run_tests())