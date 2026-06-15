from src.models.schemas import GraphExtraction
from src.core.graph import neo4j_driver

async def write_to_neo4j(extraction: GraphExtraction):
    """Writes a single chunk's extracted graph data directly into Neo4j."""
    # Use the global singleton driver
    async with neo4j_driver.session() as session:
        # Merge Nodes
        for entity in extraction.entities:
            query = f"""
            MERGE (n:`{entity.label}` {{name: $name}})
            SET n.description = $description
            """
            await session.run(query, name=entity.name, description=entity.description)
            
        # Merge Edges
        for rel in extraction.relationships:
            query = f"""
            MATCH (source {{name: $source_name}})
            MATCH (target {{name: $target_name}})
            MERGE (source)-[r:`{rel.relation_type}`]->(target)
            SET r.description = $description
            """
            await session.run(
                query,
                source_name=rel.source_entity,
                target_name=rel.target_entity,
                description=rel.description
            )