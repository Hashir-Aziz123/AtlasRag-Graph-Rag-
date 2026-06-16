from src.core.graph import neo4j_driver
from src.core.vector import qdrant_client
from src.services.embedder import generate_embedding
from src.models.schemas import ParsedQuery, RouteCategory
from config.settings import settings

async def fetch_from_graph(intent: RouteCategory, entities: list[str]) -> str:
    """Executes parameterized Cypher templates based on the LLM's routed intent."""
    if not entities:
        return ""
    
    # We grab the primary entity. If they mentioned multiple, we focus on the first for the core traversal.
    primary_entity = entities[0]
    
    # We use 'toLower(n.name) CONTAINS toLower($entity)' to handle case mismatches 
    # (e.g. user typed "nvidia" but DB has "NVIDIA")
    queries = {
        RouteCategory.ACQUISITIONS: """
            MATCH (n)-[r:ACQUIRED]->(target)
            WHERE toLower(n.name) CONTAINS toLower($entity) OR toLower(target.name) CONTAINS toLower($entity)
            RETURN n.name AS Source, type(r) AS Relationship, target.name AS Target, r.description AS Details
            LIMIT 10
        """,
        RouteCategory.PRODUCTS: """
            MATCH (n)-[r:PRODUCES|USES_TECH]->(target)
            WHERE toLower(n.name) CONTAINS toLower($entity)
            RETURN n.name AS Source, type(r) AS Relationship, target.name AS Target, r.description AS Details
            LIMIT 10
        """,
        RouteCategory.COMPETITORS: """
            MATCH (n)-[r:COMPETES_WITH]->(target)
            WHERE toLower(n.name) CONTAINS toLower($entity) OR toLower(target.name) CONTAINS toLower($entity)
            RETURN n.name AS Source, type(r) AS Relationship, target.name AS Target, r.description AS Details
            LIMIT 10
        """
    }
    
    query = queries.get(intent)
    if not query:
        return ""

    async with neo4j_driver.session() as session:
        result = await session.run(query, entity=primary_entity)
        records = await result.data()
        
    if not records:
        return ""
        
    # Format the raw JSON records into a readable string for the final LLM synthesizer
    formatted_results = [
        f"- {rec['Source']} {rec['Relationship']} {rec['Target']} (Context: {rec['Details']})" 
        for rec in records
    ]
    return "GRAPH DATA FOUND:\n" + "\n".join(formatted_results)

async def fetch_from_vector(query: str) -> str:
    """Computes the semantic vector of the query and fetches the top 3 nearest chunks from Qdrant."""
    vector = generate_embedding(query)
    
    search_results = await qdrant_client.search(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query_vector=vector,
        limit=3
    )
    
    if not search_results:
        return ""
        
    formatted_results = [f"- {hit.payload['text']}" for hit in search_results]
    return "SEMANTIC TEXT FOUND:\n" + "\n\n".join(formatted_results)

async def fetch_context(parsed_query: ParsedQuery, original_query: str) -> str:
    """
    The master fetching logic. 
    Prioritizes Graph data for specific intents, falls back to Vector data if the graph misses or the intent is general.
    """
    context = ""
    
    # 1. Try Path A: Knowledge Graph
    if parsed_query.intent != RouteCategory.GENERAL and parsed_query.entities:
        context = await fetch_from_graph(parsed_query.intent, parsed_query.entities)
        
    # 2. Try Path B: Vector Search (Fallback or General Intent)
    if not context:
        context = await fetch_from_vector(original_query)
        
    # 3. Complete Miss
    if not context:
        return "No relevant information found in the databases."
        
    return context