import unittest
from typing import List

from src.services.ingestion.chunker import StructuredChunker
from src.services.ingestion.parser import ParsedElement

class TestStructuredChunker(unittest.TestCase):
    def setUp(self):
        # Initialize with low limits to easily trigger structural boundaries
        self.chunker = StructuredChunker(max_tokens=50, overlap_tokens=10)

    def test_title_binding_and_accumulation(self):
        """Verifies that titles are stored and prepended to subsequent narrative text."""
        elements: List[ParsedElement] = [
            {"type": "Title", "text": "Risk Factors", "metadata": {"page_number": 1, "filename": "10k.pdf"}},
            {"type": "NarrativeText", "text": "Market volatility is high.", "metadata": {"page_number": 1}},
            {"type": "NarrativeText", "text": "Supply chain issues persist.", "metadata": {"page_number": 1}}
        ]
        
        chunks = self.chunker.chunk_elements(elements)
        
        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0]["text"].startswith("Section: Risk Factors"))
        self.assertIn("Market volatility", chunks[0]["text"])
        self.assertIn("Supply chain", chunks[0]["text"])
        self.assertEqual(chunks[0]["metadata"]["page_numbers"], [1])
        self.assertEqual(chunks[0]["metadata"]["filename"], "10k.pdf")

    def test_page_number_merging(self):
        """Verifies that chunks spanning multiple pages correctly merge their page metadata."""
        elements: List[ParsedElement] = [
            {"type": "NarrativeText", "text": "Sentence on page one.", "metadata": {"page_number": 1}},
            {"type": "NarrativeText", "text": "Sentence on page two.", "metadata": {"page_number": 2}},
            {"type": "NarrativeText", "text": "Sentence on page three.", "metadata": {"page_number": 3}}
        ]
        
        chunks = self.chunker.chunk_elements(elements)
        
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["metadata"]["page_numbers"], [1, 2, 3])

    def test_table_isolation(self):
        """Verifies that tables force a buffer flush and isolate themselves."""
        elements: List[ParsedElement] = [
            {"type": "Title", "text": "Financials", "metadata": {"page_number": 4}},
            {"type": "NarrativeText", "text": "Review the table below.", "metadata": {"page_number": 4}},
            {"type": "Table", "text": "Q1 | 500\nQ2 | 600", "html": "<table>...</table>", "metadata": {"page_number": 4}},
            {"type": "NarrativeText", "text": "As seen above, growth is positive.", "metadata": {"page_number": 4}}
        ]
        
        chunks = self.chunker.chunk_elements(elements)
        
        # Expected: 
        # Chunk 1: Title + Narrative
        # Chunk 2: Table
        # Chunk 3: Title + Post-table Narrative
        self.assertEqual(len(chunks), 3)
        self.assertIn("Review the table", chunks[0]["text"])
        self.assertIn("<table>", chunks[1]["text"])
        self.assertTrue(chunks[1]["text"].startswith("Section: Financials"))
        self.assertIn("growth is positive", chunks[2]["text"])

    def test_token_overflow_standard(self):
        """Verifies standard semantic splitting when accumulated paragraphs breach the limit."""
        # Generating a string that will cost roughly 30 tokens
        heavy_text = "This is a heavy paragraph. " * 6 
        
        elements: List[ParsedElement] = [
            {"type": "Title", "text": "Operations", "metadata": {"page_number": 5}},
            {"type": "NarrativeText", "text": heavy_text, "metadata": {"page_number": 5}},
            {"type": "NarrativeText", "text": heavy_text, "metadata": {"page_number": 5}}
        ]
        
        # Max tokens is 50. Two heavy paragraphs = ~60 tokens + title tokens + separator tokens.
        # It should split them across two chunks, retaining the title in both.
        chunks = self.chunker.chunk_elements(elements)
        
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0]["text"].startswith("Section: Operations"))
        self.assertTrue(chunks[1]["text"].startswith("Section: Operations"))

    def test_fallback_splitting_oversized_element(self):
        """Verifies that a single massive element triggers the token-level slicer."""
        massive_text = "Overflow word. " * 50 # ~100 tokens, exceeds the 50 max_tokens limit
        
        elements: List[ParsedElement] = [
            {"type": "NarrativeText", "text": massive_text, "metadata": {"page_number": 6}}
        ]
        
        chunks = self.chunker.chunk_elements(elements)
        
        # Given max=50 and overlap=10 (stride=40), 100 tokens should yield roughly 3 chunks.
        self.assertGreater(len(chunks), 1)
        
        # Verify the chunks don't exceed the limit
        for chunk in chunks:
            token_count = len(self.chunker.tokenizer.encode(chunk["text"], disallowed_special=()))
            self.assertLessEqual(token_count, 50)
            self.assertEqual(chunk["metadata"]["page_numbers"], [6])

if __name__ == "__main__":
    unittest.main()