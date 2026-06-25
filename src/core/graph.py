import os
import logging
from neo4j import AsyncGraphDatabase, AsyncDriver
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD environment variable is missing.")

class GraphDBDriver:
    _driver: AsyncDriver = None

    @classmethod
    def get_driver(cls) -> AsyncDriver:
        if cls._driver is None:
            cls._driver = AsyncGraphDatabase.driver(
                NEO4J_URI, 
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
        return cls._driver

    @classmethod
    async def close_driver(cls):
        if cls._driver is not None:
            await cls._driver.close()
            cls._driver = None

neo4j_driver = GraphDBDriver.get_driver()

async def init_neo4j_schema() -> None:
    """
    Idempotent schema initialization.
    Creates the required full-text indexes and constraints for the retrieval pipeline.
    """
    valid_labels = [
        "Company", "Person", "Product", "Technology", 
        "Financial_Metric", "Location", "Risk_Factor", "Market_Sector"
    ]
    
    label_string = "|".join(valid_labels)
    
    index_query = f"""
    CREATE FULLTEXT INDEX entity_names IF NOT EXISTS 
    FOR (n:{label_string}) ON EACH [n.name]
    """
    
    constraint_query = """
    CREATE CONSTRAINT document_name_unique IF NOT EXISTS 
    FOR (d:Document) REQUIRE d.name IS UNIQUE
    """
    
    try:
        async with neo4j_driver.session() as session:
            await session.run(index_query)
            await session.run(constraint_query)
        logger.info("[*] Neo4j schema initialized: Full-text indexes and constraints verified.")
    except Exception as e:
        logger.error(f"[!] Failed to initialize Neo4j schema: {e}")
        raise