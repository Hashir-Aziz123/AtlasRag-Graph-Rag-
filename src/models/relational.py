import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship as sa_relationship
from src.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    content_hash = Column(String, unique=True, nullable=False)
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    chunks = sa_relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    jobs = sa_relationship("IngestionJob", back_populates="document", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"))
    text_content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    section_name = Column(String, nullable=True)

    document = sa_relationship("Document", back_populates="chunks")

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"))
    status = Column(String, default="PENDING")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    document = sa_relationship("Document", back_populates="jobs")