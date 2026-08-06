"""
PANDORA Content Service Content Models
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class ContentType(str, Enum):
    """Types of content supported."""
    
    PDF = "pdf"
    EPUB = "epub"
    DOC = "doc"
    DOCX = "docx"
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"


class ContentStatus(str, Enum):
    """Processing status of content."""
    
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class Document(Base, TimestampMixin):
    """Document model for storing content metadata."""
    
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_title", "title"),
        Index("ix_documents_content_type", "content_type"),
        Index("ix_documents_status", "status"),
        Index("ix_documents_owner_id", "owner_id"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    checksum: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=ContentStatus.UPLOADED,
        nullable=False,
    )
    language: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    word_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    extraction_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    extraction_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    license_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    source_url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    collections: Mapped[list["Collection"]] = relationship(
        "CollectionDocument",
        back_populates="document",
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title})>"


class DocumentVersion(Base, TimestampMixin):
    """Version tracking for documents."""
    
    __tablename__ = "document_versions"
    __table_args__ = (
        Index("ix_document_versions_document_id", "document_id"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    checksum: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    change_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="versions",
    )
    
    def __repr__(self) -> str:
        return f"<DocumentVersion(id={self.id}, v{self.version_number})>"


class Collection(Base, TimestampMixin):
    """Collection model for grouping documents."""
    
    __tablename__ = "collections"
    __table_args__ = (
        Index("ix_collections_name", "name"),
        Index("ix_collections_owner_id", "owner_id"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    
    # Relationships
    documents: Mapped[list["CollectionDocument"]] = relationship(
        "CollectionDocument",
        back_populates="collection",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, name={self.name})>"


class CollectionDocument(Base):
    """Association table for documents in collections."""
    
    __tablename__ = "collection_documents"
    
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("collections.id"),
        primary_key=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        primary_key=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    order_index: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection",
        back_populates="documents",
    )
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="collections",
    )


class Tag(Base, TimestampMixin):
    """Tag model for categorizing content."""
    
    __tablename__ = "tags"
    __table_args__ = (
        Index("ix_tags_name", "name", unique=True),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"
