import pytest
from sqlalchemy import text
from src.core.database import engine
from src.core.vector import qdrant_client
from src.core.graph import neo4j_driver


pytestmark = pytest.mark.asyncio

async def test_postgres_connection():
    """Verify async connection to the PostgreSQL container."""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version();"))
        row = result.fetchone()
        assert row is not None
        assert "PostgreSQL" in row[0]

def test_qdrant_connection():
    """Verify connection to the Qdrant vector database client."""
    collections = qdrant_client.get_collections()
    assert collections is not None
    assert hasattr(collections, "collections")

def test_neo4j_connection():
    """Verify Bolt protocol connectivity to the Neo4j instance."""
    with neo4j_driver.session() as session:
        result = session.run("RETURN 'Connection Successful' as msg")
        record = result.single()
        assert record is not None
        assert record["msg"] == "Connection Successful"