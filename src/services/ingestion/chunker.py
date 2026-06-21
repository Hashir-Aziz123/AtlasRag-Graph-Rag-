import logging
from typing import List, Dict, Any, TypedDict, Optional
import tiktoken

from src.services.ingestion.parser import ParsedElement

logger = logging.getLogger(__name__)

class DocumentChunk(TypedDict):
    text: str
    metadata: Dict[str, Any]

class StructuredChunker:
    """
    State machine that processes a topological stream of document elements and 
    binds them into cohesive blocks strictly under the token limit, 
    preserving document hierarchy and tabular matrices.
    """
    
    def __init__(self, max_tokens: int = 400, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.separator = "\n\n"
        
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.error("Failed to initialize tiktoken encoder.", exc_info=True)
            raise

        self.separator_tokens = len(self.tokenizer.encode(self.separator, disallowed_special=()))
        self._reset_state()

    def _reset_state(self) -> None:
        """Resets the accumulator buffer while retaining the active structural context."""
        self.buffer_texts: List[str] = []
        self.buffer_tokens: int = 0
        self.current_metadata: Dict[str, Any] = {}

    def _merge_metadata(self, new_meta: Dict[str, Any]) -> None:
        """Merges new element metadata into the active buffer metadata to track page ranges."""
        if "filename" in new_meta and new_meta["filename"] and "filename" not in self.current_metadata:
            self.current_metadata["filename"] = new_meta["filename"]

        if "page_number" in new_meta and new_meta["page_number"] is not None:
            if "page_numbers" not in self.current_metadata:
                self.current_metadata["page_numbers"] = set()
            self.current_metadata["page_numbers"].add(new_meta["page_number"])

    def _count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text, disallowed_special=()))

    def _flush_buffer(self) -> Optional[DocumentChunk]:
        """Compiles the accumulated elements into a complete chunk and clears the buffer."""
        if not self.buffer_texts:
            return None

        compiled_text = self.separator.join(self.buffer_texts)
        
        chunk_meta = self.current_metadata.copy()
        # Convert the dynamic set back into a JSON-serializable sorted list for the vector store
        if "page_numbers" in chunk_meta and isinstance(chunk_meta["page_numbers"], set):
            chunk_meta["page_numbers"] = sorted(list(chunk_meta["page_numbers"]))
        
        chunk: DocumentChunk = {
            "text": compiled_text,
            "metadata": chunk_meta
        }
        
        self._reset_state()
        return chunk

    def _standardize_metadata(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Converts singular element metadata into the standard list format."""
        standardized = {}
        if "filename" in meta and meta["filename"]:
            standardized["filename"] = meta["filename"]
        if "page_number" in meta and meta["page_number"] is not None:
            standardized["page_numbers"] = [meta["page_number"]]
        return standardized

    def _apply_fallback_splitting(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Forcefully splits an oversized element using strict token boundaries.
        Used exclusively as a last resort for massive elements (e.g., giant HTML tables) 
        that cannot be structurally parsed further without breaching embedder limits.
        """
        logger.warning(f"Structural element exceeded {self.max_tokens} tokens. Applying token-level fallback slicing.")
        
        tokens = self.tokenizer.encode(text, disallowed_special=())
        stride = self.max_tokens - self.overlap_tokens
        if stride <= 0:
            stride = self.max_tokens

        split_chunks: List[DocumentChunk] = []
        standard_meta = self._standardize_metadata(metadata)
        
        for i in range(0, len(tokens), stride):
            chunk_tokens = tokens[i:i + self.max_tokens]
            # Decode token sequence back to a string. 
            # tiktoken safely handles partial multi-byte character slices internally.
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            split_chunks.append({
                "text": chunk_text,
                "metadata": standard_meta.copy()
            })

        return split_chunks

    def chunk_elements(self, elements: List[ParsedElement]) -> List[DocumentChunk]:
        """
        Iterates through parsed document elements, binding structural context (titles) 
        to narrative blocks and isolating tabular matrices.
        """
        final_chunks: List[DocumentChunk] = []
        active_title: str = ""

        for element in elements:
            el_type = element.get("type", "Unknown")
            el_text = element.get("text", "")
            el_html = element.get("html", "")
            el_meta = element.get("metadata", {})

            # 1. Title Boundary: Flush previous block, update context tracker
            if el_type in ("Title", "Header"):
                if flush_result := self._flush_buffer():
                    final_chunks.append(flush_result)
                active_title = el_text
                self._merge_metadata(el_meta)
                continue

            # 2. Table Boundary: Isolate matrices immediately
            if el_type == "Table":
                if flush_result := self._flush_buffer():
                    final_chunks.append(flush_result)

                # Prioritize HTML for structural retention, fallback to raw text
                table_content = el_html if el_html else el_text
                if active_title:
                    table_content = f"Section: {active_title}\n\n{table_content}"

                table_tokens = self._count_tokens(table_content)

                if table_tokens > self.max_tokens:
                    final_chunks.extend(self._apply_fallback_splitting(table_content, el_meta))
                else:
                    final_chunks.append({"text": table_content, "metadata": self._standardize_metadata(el_meta)})
                continue

            # 3. Narrative Assembly
            content_to_add = el_text
            
            # If starting a fresh buffer, bind the active title to the top
            if not self.buffer_texts and active_title:
                content_to_add = f"Section: {active_title}\n\n{content_to_add}"

            element_tokens = self._count_tokens(content_to_add)
            
            # Factor in the separator token cost if the buffer isn't empty
            cost_to_add = element_tokens
            if self.buffer_tokens > 0:
                cost_to_add += self.separator_tokens

            # Edge Case: A single narrative paragraph is massive
            if element_tokens > self.max_tokens:
                if flush_result := self._flush_buffer():
                    final_chunks.append(flush_result)
                final_chunks.extend(self._apply_fallback_splitting(content_to_add, el_meta))
                continue

            # Standard Case: Check if adding this element breaches the ceiling
            if self.buffer_tokens + cost_to_add > self.max_tokens:
                if flush_result := self._flush_buffer():
                    final_chunks.append(flush_result)
                
                # Start the new buffer with the title re-attached
                if active_title:
                    content_to_add = f"Section: {active_title}\n\n{el_text}"
                element_tokens = self._count_tokens(content_to_add)
                cost_to_add = element_tokens

            # Accumulate
            self.buffer_texts.append(content_to_add)
            self.buffer_tokens += cost_to_add
            self._merge_metadata(el_meta)

        # Final flush for any remaining stragglers
        if flush_result := self._flush_buffer():
            final_chunks.append(flush_result)

        logger.info(f"Assembled {len(elements)} raw elements into {len(final_chunks)} structured chunks.")
        return final_chunks