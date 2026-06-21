import logging
from typing import Dict, Any
from src.models.schemas import GraphExtraction
from src.core.graph import neo4j_driver

logger = logging.getLogger(__name__)

async def write_to_neo4j(extraction: GraphExtraction, metadata: Dict[str, Any]) -> None:
    """
    Writes a single chunk's extracted graph data into Neo4j and establishes 
    strict data lineage mapping back to the source document and page numbers.
    """
    filename = metadata.get("filename", "unknown_document")
    page_numbers = metadata.get("page_numbers", [])

    # Cache entity labels locally to prevent full database scans during edge creation
    entity_label_map = {entity.name: entity.label for entity in extraction.entities}

    async with neo4j_driver.session() as session:
        # 1. Merge Entities and Link to Document (Provenance)
        for entity in extraction.entities:
            query = f"""
            MERGE (n:`{entity.label}` {{name: $name}})
            SET n.description = $description
            WITH n
            MERGE (d:Document {{name: $filename}})
            MERGE (n)-[m:MENTIONED_IN]->(d)
            SET m.page_numbers = $page_numbers
            """
            await session.run(
                query, 
                name=entity.name, 
                description=entity.description,
                filename=filename,
                page_numbers=page_numbers
            )
            
        # 2. Merge Edges between Entities
        for rel in extraction.relationships:
            source_label = entity_label_map.get(rel.source_entity)
            target_label = entity_label_map.get(rel.target_entity)

            # Construct MATCH clauses dynamically. Cypher requires labels to be 
            # hardcoded in the query string; they cannot be passed as parameters.
            source_match = f"source:`{source_label}`" if source_label else "source"
            target_match = f"target:`{target_label}`" if target_label else "target"

            query = f"""
            MATCH ({source_match} {{name: $source_name}})
            MATCH ({target_match} {{name: $target_name}})
            MERGE (source)-[r:`{rel.relation_type}`]->(target)
            SET r.description = $description
            """
            
            await session.run(
                query,
                source_name=rel.source_entity,
                target_name=rel.target_entity,
                description=rel.description
            )