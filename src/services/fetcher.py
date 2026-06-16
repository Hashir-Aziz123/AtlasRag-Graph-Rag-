import asyncio
from src.core.graph import neo4j_driver
from src.core.vector import qdrant_client
from src.services.embedder import generate_embedding
from src.models.schemas import ParsedQuery, RouteCategory
from config.settings import settings

async def fetch_from_graph(intent: RouteCategory, entities: list[str]) -> str:
    """Executes optimized Cypher templates using Full-Text Search and dynamic pathing."""
    if not entities:
        return ""

    async with neo4j_driver.session() as session:
        # --- Multi-Entity Pathing ---
        if len(entities) >= 2:
            # We append '~' to enable Lucene fuzzy matching (typo tolerance)
            query = """
                CALL db.index.fulltext.queryNodes("entity_names", $e1) YIELD node AS source
                CALL db.index.fulltext.queryNodes("entity_names", $e2) YIELD node AS target
                MATCH p = shortestPath((source)-[*]-(target))
                RETURN [x IN nodes(p) | x.name] AS Path, [x IN relationships(p) | type(x)] AS Relationships
                LIMIT toInteger($limit)
            """
            result = await session.run(
                query, 
                e1=f"{entities[0]}~", 
                e2=f"{entities[1]}~", 
                limit=settings.GRAPH_RETURN_LIMIT
            )
            records = await result.data()
            if not records:
                return ""
            
            formatted = [f"- Path: {' -> '.join(rec['Path'])} (Relations: {', '.join(rec['Relationships'])})" for rec in records]
            return "GRAPH TOPOLOGY (MULTI-ENTITY):\n" + "\n".join(formatted)

        # --- Single-Entity Templates ---
        # Fuzzy match the primary entity against the Lucene index
        primary_entity = f"{entities[0]}~"
        
        queries = {
            RouteCategory.ACQUISITIONS: """
                CALL db.index.fulltext.queryNodes("entity_names", $entity) YIELD node AS n
                MATCH (n)-[r:ACQUIRED]->(target)
                RETURN n.name AS Source, type(r) AS Relationship, target.name AS Target, r.description AS Details
                LIMIT toInteger($limit)
            """,
            RouteCategory.PRODUCTS: """
                CALL db.index.fulltext.queryNodes("entity_names", $entity) YIELD node AS n
                MATCH (n)-[r:PRODUCES|USES_TECH]->(target)
                RETURN n.name AS Source, type(r) AS Relationship, target.name AS Target, r.description AS Details
                LIMIT toInteger($limit)
            """,
            RouteCategory.COMPETITORS: """
                CALL db.index.fulltext.queryNodes("entity_names", $entity) YIELD node AS n
                MATCH (n)-[r:COMPETES_WITH]->(target)
                RETURN n.name AS Source, type(r) AS Relationship, target.name AS Target, r.description AS Details
                LIMIT toInteger($limit)
            """
        }
        
        query = queries.get(intent)
        if not query:
            return ""

        result = await session.run(query, entity=primary_entity, limit=settings.GRAPH_RETURN_LIMIT)
        records = await result.data()
            
        if not records:
            return ""
            
        formatted = [f"- {rec['Source']} {rec['Relationship']} {rec['Target']} (Context: {rec['Details']})" for rec in records]
        return "GRAPH DATA FOUND:\n" + "\n".join(formatted)

async def fetch_from_vector(query: str) -> str:
    """Computes semantic vector and fetches nearest chunks from Qdrant."""
    vector = generate_embedding(query)
    
    search_results = await qdrant_client.search(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query_vector=vector,
        limit=settings.VECTOR_RETURN_LIMIT
    )
    
    if not search_results:
        return ""
        
    formatted = [f"- {hit.payload['text']}" for hit in search_results]
    return "SEMANTIC TEXT FOUND:\n" + "\n\n".join(formatted)

async def fetch_context(parsed_query: ParsedQuery, original_query: str) -> str:
    """
    Executes Hybrid RAG via asyncio.gather(). 
    Fires off graph and vector queries simultaneously, then fuses the results.
    """
    # We always want the vector context to capture the nuance
    tasks = [fetch_from_vector(original_query)]
    
    # If the LLM router gave us a specific intent and entities, we fire off the Graph query too
    has_graph_intent = parsed_query.intent != RouteCategory.GENERAL and parsed_query.entities
    if has_graph_intent:
        tasks.append(fetch_from_graph(parsed_query.intent, parsed_query.entities))
        
    # Execute all database calls concurrently
    results = await asyncio.gather(*tasks)
    
    vector_context = results[0]
    graph_context = results[1] if has_graph_intent else ""
    
    # Fuse the contexts
    fused_context = f"{graph_context}\n\n{vector_context}".strip()
    
    if not fused_context:
        return "No relevant information found in the databases."
        
    return fused_context