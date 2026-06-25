import asyncio
import re

from sqlalchemy.future import select

from src.core.graph import neo4j_driver
from src.core.vector import qdrant_client
from src.core.embedder import generate_embedding
from src.core.database import async_session_maker
from src.models.schemas import ParsedQuery, RouteCategory
from src.models.relational import Chunk
from config.settings import settings
from qdrant_client.models import Filter, FieldCondition, MatchValue

def clean_lucene_query(text: str) -> str:
    """Strips hyphens and special characters that act as logical operators in Lucene."""
    cleaned = re.sub(r'[^\w\s]', ' ', text)
    return cleaned.strip()

async def fetch_from_graph(intent: RouteCategory, entities: list[str]) -> str:
    """Executes optimized Cypher templates using Full-Text Search, dynamic pathing, and provenance tracking."""
    if not entities:
        return ""

    async with neo4j_driver.session() as session:
        # --- Multi-Entity Pathing ---
        if len(entities) >= 2:
            query = """
                CALL db.index.fulltext.queryNodes("entity_names", $e1) YIELD node AS source
                CALL db.index.fulltext.queryNodes("entity_names", $e2) YIELD node AS target
                MATCH p = shortestPath((source)-[*]-(target))
                OPTIONAL MATCH (source)-[m1:MENTIONED_IN]->(d1:Document)
                OPTIONAL MATCH (target)-[m2:MENTIONED_IN]->(d2:Document)
                RETURN [x IN nodes(p) | coalesce(x.name, 'Unknown')] AS Path, 
                       [x IN relationships(p) | type(x)] AS Relationships,
                       collect(DISTINCT {doc: d1.name, pages: m1.page_numbers}) AS SourceDocs,
                       collect(DISTINCT {doc: d2.name, pages: m2.page_numbers}) AS TargetDocs
                LIMIT toInteger($limit)
            """
            result = await session.run(
                query, 
                e1=f"{clean_lucene_query(entities[0])}~", 
                e2=f"{clean_lucene_query(entities[1])}~", 
                limit=settings.GRAPH_RETURN_LIMIT
            )
            records = await result.data()
            if not records:
                return ""
            
            formatted = []
            for rec in records:
                path_str = " -> ".join(rec['Path'])
                rel_str = ", ".join(rec['Relationships'])
                
                # Format citations safely in Python
                docs_list = []
                for c in rec.get('SourceDocs', []) + rec.get('TargetDocs', []):
                    if c and c.get('doc'):
                        pages = c.get('pages') or []
                        pages_str = ", ".join(str(p) for p in pages)
                        docs_list.append(f"{c['doc']} (pg [{pages_str}])")
                
                docs_str = "; ".join(set(docs_list)) if docs_list else "Unknown Source"
                formatted.append(f"- Path: {path_str} (Relations: {rel_str}) [Cited In: {docs_str}]")
                
            return "GRAPH TOPOLOGY (MULTI-ENTITY):\n" + "\n".join(formatted)

        # --- Single-Entity Templates ---
        primary_entity = f"{clean_lucene_query(entities[0])}~"
        
        # Notice we are returning a map {doc: d.name, pages: m.page_numbers} instead of string concatenation
        base_query_template = """
            CALL db.index.fulltext.queryNodes("entity_names", $entity) YIELD node AS n
            MATCH (n)-[r:{rel_types}]-(target)
            OPTIONAL MATCH (n)-[m:MENTIONED_IN]->(d:Document)
            RETURN coalesce(startNode(r).name, 'Unknown') AS Source, 
                   type(r) AS Relationship, 
                   coalesce(endNode(r).name, 'Unknown') AS Target, 
                   coalesce(r.description, '') AS Details,
                   collect(DISTINCT {{doc: d.name, pages: m.page_numbers}}) AS Citations
            LIMIT toInteger($limit)
        """
        
        queries = {
            RouteCategory.ACQUISITIONS: base_query_template.format(rel_types="ACQUIRED"),
            RouteCategory.PRODUCTS: base_query_template.format(rel_types="PRODUCES|USES_TECH"),
            RouteCategory.COMPETITORS: base_query_template.format(rel_types="COMPETES_WITH")
        }
        
        query = queries.get(intent)
        if not query:
            return ""

        result = await session.run(query, entity=primary_entity, limit=settings.GRAPH_RETURN_LIMIT)
        records = await result.data()
            
        if not records:
            return ""
            
        formatted = []
        for rec in records:
            citations_list = []
            for c in rec.get('Citations', []):
                if c and c.get('doc'):
                    pages = c.get('pages') or []
                    pages_str = ", ".join(str(p) for p in pages)
                    citations_list.append(f"{c['doc']} (pg [{pages_str}])")
            
            citations_str = "; ".join(set(citations_list)) if citations_list else "Unknown Source"
            formatted.append(f"- {rec['Source']} {rec['Relationship']} {rec['Target']} (Context: {rec['Details']}) [Citations: {citations_str}]")
            
        return "GRAPH DATA FOUND:\n" + "\n".join(formatted)

async def fetch_from_vector(query: str, target_document: str | None = None) -> str:
    """
    Computes semantic vector, applies optional metadata filters, 
    fetches UUID pointers from Qdrant, and dereferences them against PostgreSQL.
    """
    vector = await asyncio.to_thread(generate_embedding, query)
    
    query_filter = None
    if target_document:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="filename",
                    match=MatchValue(value=target_document)
                )
            ]
        )
    
    search_results = await qdrant_client.search(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query_vector=vector,
        query_filter=query_filter,
        limit=settings.VECTOR_RETURN_LIMIT
    )
    
    if not search_results:
        return ""
        
    chunk_ids = [str(hit.id) for hit in search_results]
    
    async with async_session_maker() as session:
        stmt = select(Chunk.text_content).where(Chunk.id.in_(chunk_ids))
        result = await session.execute(stmt)
        text_contents = result.scalars().all()
        
    if not text_contents:
        return ""
        
    formatted = [f"- {text}" for text in text_contents]
    return "SEMANTIC TEXT FOUND:\n" + "\n\n".join(formatted)

async def fetch_context(parsed_query: ParsedQuery, original_query: str) -> str:
    """
    Executes Hybrid RAG via asyncio.gather(). 
    Fires off graph and vector queries simultaneously, then fuses the results.
    """
    tasks = [fetch_from_vector(original_query, parsed_query.target_document)]
    
    has_graph_intent = parsed_query.intent != RouteCategory.GENERAL and parsed_query.entities
    if has_graph_intent:
        tasks.append(fetch_from_graph(parsed_query.intent, parsed_query.entities))
        
    results = await asyncio.gather(*tasks)
    
    vector_context = results[0]
    graph_context = results[1] if has_graph_intent else ""
    
    fused_context = f"{graph_context}\n\n{vector_context}".strip()
    
    if not fused_context:
        return "No relevant information found in the databases."
        
    return fused_context