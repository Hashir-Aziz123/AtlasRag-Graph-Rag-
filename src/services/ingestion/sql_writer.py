import hashlib
import os
import uuid
import logging
from typing import List, Dict, Any

from sqlalchemy.future import select

from src.models.relational import Document, Chunk
from src.core.database import async_session_maker

logger = logging.getLogger(__name__)

def compute_file_hash(file_path: str) -> str:
    """
    Computes a SHA-256 hash of the raw file to serve as a deterministic 
    fingerprint for cryptographic deduplication.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as file_buffer:
        for byte_block in iter(lambda: file_buffer.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

async def check_document_exists(file_path: str) -> bool:
    """Queries PostgreSQL to determine if this file signature already exists."""
    content_hash = compute_file_hash(file_path)
    
    async with async_session_maker() as session:
        query = select(Document).where(Document.content_hash == content_hash)
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

async def write_chunks_to_sql(file_path: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Persists the source document and its structural chunks into PostgreSQL.
    Returns the enriched chunks array, appending the SQL-generated UUID to each chunk.
    """
    content_hash = compute_file_hash(file_path)
    filename = os.path.basename(file_path)
    enriched_chunks = []

    async with async_session_maker() as session:
        new_doc = Document(
            filename=filename,
            content_hash=content_hash,
            metadata_json={"chunk_count": len(chunks)}
        )
        session.add(new_doc)
        
        # Flush to ensure the Document UUID is generated for the foreign key constraints
        await session.flush() 

        db_chunks = []
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            
            # Explicitly generate the UUID in memory to bypass SQLAlchemy flush dependencies
            chunk_id = str(uuid.uuid4())
            
            db_chunk = Chunk(
                id=chunk_id,
                document_id=new_doc.id,
                text_content=chunk.get("text", ""),
                page_numbers=metadata.get("page_numbers", []),
                section_name=None 
            )
            db_chunks.append(db_chunk)
            
            enriched_chunks.append({
                "chunk_id": chunk_id,
                "text": db_chunk.text_content,
                "metadata": metadata
            })

        session.add_all(db_chunks)
        await session.commit()

        logger.info("Persisted Document '%s' and %d chunks to PostgreSQL.", filename, len(chunks))
        return enriched_chunks