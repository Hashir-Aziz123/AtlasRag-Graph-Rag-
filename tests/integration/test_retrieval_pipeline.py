import os
import sys
import unittest
import asyncio

# Resolve project root dynamically for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(PROJECT_ROOT)

from sqlalchemy.future import select

from src.models.schemas import ParsedQuery, RouteCategory
from src.services.retrieval.router import route_user_query
from src.services.retrieval.fetcher import fetch_context
from src.core.database import async_session_maker
from src.models.relational import Document

class TestRetrievalPipelineE2E(unittest.TestCase):
    """
    Validates the federated retrieval architecture.
    Runs inside a single event loop to prevent Neo4j Proactor socket closures on Windows.
    """

    def test_retrieval_architecture(self):
        """Executes all async tests sequentially in one protected event loop."""
        asyncio.run(self._async_runner())

    async def _async_runner(self):
        # 1. Dynamically fetch an actual ingested document name from PostgreSQL
        async with async_session_maker() as session:
            result = await session.execute(select(Document.filename).limit(1))
            actual_filename = result.scalar_one_or_none()

        if not actual_filename:
            self.skipTest("[!] Database is empty. Run ingestion first to seed data.")
            return

        print(f"\n[*] Found active document in DB for testing: {actual_filename}")

        # 2. Run the suite sequentially using the dynamic filename
        await self._test_1_router(actual_filename)
        await self._test_2_fetcher(actual_filename)
        await self._test_3_full_lifecycle()

    async def _test_1_router(self, target_filename: str):
        """Verifies that the LLM router accurately extracts entities and document constraints."""
        print("[*] Testing Query Router...")
        
        query = f"What products and technologies did NVIDIA announce in {target_filename}?"
        parsed_query = await route_user_query(query)
        
        self.assertIsInstance(parsed_query, ParsedQuery)
        
        self.assertEqual(parsed_query.intent, RouteCategory.PRODUCTS)
        
        extracted_entities = [e.upper() for e in parsed_query.entities]
        self.assertIn("NVIDIA", extracted_entities)
        
        # Verify the LLM successfully caught the dynamic filename constraint
        self.assertEqual(parsed_query.target_document, target_filename)

    async def _test_2_fetcher(self, target_filename: str):
        """Verifies Qdrant pointer dereferencing and Neo4j provenance traversal."""
        print("[*] Testing Federated Fetcher (Vector + Graph)...")
        
        mock_parsed_query = ParsedQuery(
            intent=RouteCategory.PRODUCTS,
            entities=["NVIDIA"],
            target_document=target_filename
        )
        
        # Using a broad query so it finds a vector regardless of which document you ingested
        original_user_query = "What technology, hardware, or research is mentioned?"
        
        fused_context = await fetch_context(mock_parsed_query, original_user_query)
        
        self.assertIsNotNone(fused_context)
        self.assertNotEqual(fused_context, "No relevant information found in the databases.")
        
        self.assertIn(
            "SEMANTIC TEXT FOUND", 
            fused_context, 
            "Vector retrieval failed or Postgres pointer dereferencing returned empty."
        )

    async def _test_3_full_lifecycle(self):
        """Executes the full router-to-fetcher pipeline without a specific document constraint."""
        print("[*] Testing Full E2E Retrieval Lifecycle...")
        
        query = "Tell me about NVIDIA's competitors and market rivals."
        
        parsed_query = await route_user_query(query)
        self.assertEqual(parsed_query.intent, RouteCategory.COMPETITORS)
        self.assertIsNone(parsed_query.target_document)
        
        fused_context = await fetch_context(parsed_query, query)
        
        self.assertIsInstance(fused_context, str)
        self.assertGreater(
            len(fused_context), 
            50, 
            "Fused context is suspiciously short. Retrieval may have failed."
        )

if __name__ == "__main__":
    unittest.main()