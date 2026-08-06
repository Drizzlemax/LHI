"""
PANDORA Content Service Content Models
Core models for the content management system.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class ContentCategory(str, Enum):
    """High-level content categories."""
    
    BOOK = "book"
    ARTICLE = "article"
    VIDEO = "video"
    COURSE = "course"
    LESSON = "lesson"
    QUIZ = "quiz"
    INTERACTIVE = "interactive"
    DOCUMENT = "document"


class ContentType(str, Enum):
    """Specific content format types."""
    
    # Documents
    PDF = "pdf"
    EPUB = "epub"
    DOC = "doc"
    DOCX = "docx"
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    
    # Media
    MP4 = "mp4"
    WEBM = "webm"
    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    
    # Interactive
    HTML5 = "html5"
    SCORM = "scorm"
    XAPI = "xapi"
    
    # Course formats
    SCORM_COURSE = "scorm_course"
    XAPI_COURSE = "xapi_course"


class ContentStatus(str, Enum):
    """Processing status of content."""
    
    DRAFT = "draft"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class EducationLevel(str, Enum):
    """Education levels for content classification."""
    
    ELEMENTARY = "elementary"           # K-5
    MIDDLE_SCHOOL = "middle_school"     # 6-8
    HIGH_SCHOOL = "high_school"         # 9-12
    UNDERGRADUATE = "undergraduate"      # College
    GRADUATE = "graduate"                # Master's
    DOCTORAL = "doctoral"               # PhD
    PROFESSIONAL = "professional"        # Continuing education
    ALL_LEVELS = "all_levels"           # Cross-level content


class Content(Base, TimestampMixin):
    """
    Main Content model representing educational materials.
    
    This is the central entity for all content types (books, articles,
    videos, courses, lessons, quizzes, interactive content, documents).
    """
    
    __tablename__ = "contents"
    __table_args__ = (
        Index("ix_contents_title", "title"),
        Index("ix_contents_category", "category"),
        Index("ix_contents_content_type", "content_type"),
        Index("ix_contents_status", "status"),
        Index("ix_contents_education_level", "education_level"),
        Index("ix_contents_owner_id", "owner_id"),
        Index("ix_contents_language", "language"),
        Index("ix_contents_is_public", "is_public"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Basic Info
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Classification
    category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ContentCategory.DOCUMENT,
    )
    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    education_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Content Details
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
    )
    
    # File/Storage Info
    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    storage_key: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    checksum: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    
    # Media Info (for videos, courses)
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
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
    
    # Status & Visibility
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ContentStatus.DRAFT,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_premium: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    
    # Ownership
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    creator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Licensing & Source
    license_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    source_url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    source_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    
    # Extracted/Synthesized Content
    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    extraction_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Thumbnail & Media
    thumbnail_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    preview_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    
    # Metadata (flexible JSON for additional data)
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    
    # Tags
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    
    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Relationships
    metadata_record: Mapped["ContentMetadata | None"] = relationship(
        "ContentMetadata",
        back_populates="content",
        uselist=False,
        cascade="all, delete-orphan",
    )
    vector_record: Mapped["ContentVector | None"] = relationship(
        "ContentVector",
        back_populates="content",
        uselist=False,
        cascade="all, delete-orphan",
    )
    media_assets: Mapped[list["MediaAsset"]] = relationship(
        "MediaAsset",
        back_populates="content",
        cascade="all, delete-orphan",
    )
    versions: Mapped[list["ContentVersion"]] = relationship(
        "ContentVersion",
        back_populates="content",
        cascade="all, delete-orphan",
    )
    collections: Mapped[list["ContentCollection"]] = relationship(
        "ContentCollection",
        back_populates="content",
    )
    learning_paths: Mapped[list["LearningPathContent"]] = relationship(
        "LearningPathContent",
        back_populates="content",
    )
    tags_relation: Mapped[list["Tag"]] = relationship(
        "Tag",
        back_populates="contents",
    )
    
    def __repr__(self) -> str:
        return f"<Content(id={self.id}, title={self.title}, category={self.category})>"
    
    @property
    def is_available(self) -> bool:
        """Check if content is available for consumption."""
        return self.status == ContentStatus.READY.value or self.status == ContentStatus.PUBLISHED.value


class ContentMetadata(Base, TimestampMixin):
    """
    Metadata for Content including authors, publication info, and ratings.
    """
    
    __tablename__ = "content_metadata"
    __table_args__ = (
        Index("ix_content_metadata_content_id", "content_id", unique=True),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    
    # Authors & Attribution
    authors: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    author_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=True,
    )
    editors: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    translators: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    illustrators: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    
    # Publication Info
    publication_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    publication_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    publisher: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    isbn: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    issn: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    doi: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    
    # Subject & Classification
    subjects: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    keywords: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    
    # Licensing
    license_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    rights_holder: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    
    # Ratings & Reviews
    average_rating: Mapped[float | None] = mapped_column(
        default=None,
        nullable=True,
    )
    rating_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    download_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    
    # Additional Metadata
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    
    # Relationships
    content: Mapped["Content"] = relationship(
        "Content",
        back_populates="metadata_record",
    )
    
    def __repr__(self) -> str:
        return f"<ContentMetadata(id={self.id}, content_id={self.content_id})>"


class ContentVector(Base, TimestampMixin):
    """
    Vector embeddings for content, used for semantic search.
    """
    
    __tablename__ = "content_vectors"
    __table_args__ = (
        Index("ix_content_vectors_content_id", "content_id", unique=True),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    
    # Embedding fields
    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    chunk_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # For vector storage (use pgvector in production)
    vector: Mapped[list[float] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    vector_dimensions: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Metadata for retrieval
    start_char: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    end_char: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Relationships
    content: Mapped["Content"] = relationship(
        "Content",
        back_populates="vector_record",
    )
    
    def __repr__(self) -> str:
        return f"<ContentVector(id={self.id}, content_id={self.content_id}, chunk={self.chunk_index})>"


class ContentVersion(Base, TimestampMixin):
    """Version tracking for content updates."""
    
    __tablename__ = "content_versions"
    __table_args__ = (
        Index("ix_content_versions_content_id", "content_id"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    # Version snapshot
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    storage_key: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    checksum: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Change tracking
    change_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    change_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Relationships
    content: Mapped["Content"] = relationship(
        "Content",
        back_populates="versions",
    )
    
    def __repr__(self) -> str:
        return f"<ContentVersion(id={self.id}, content_id={self.content_id}, v{self.version_number})>"


class MediaAsset(Base, TimestampMixin):
    """
    Media assets associated with content (images, videos, audio, files).
    """
    
    __tablename__ = "media_assets"
    __table_args__ = (
        Index("ix_media_assets_content_id", "content_id"),
        Index("ix_media_assets_asset_type", "asset_type"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Asset Info
    asset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Location & Storage
    url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    storage_key: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    
    # Technical Details
    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    width: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    height: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        nullable=True,
    )
    
    # Usage
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    
    # Relationships
    content: Mapped["Content"] = relationship(
        "Content",
        back_populates="media_assets",
    )
    
    def __repr__(self) -> str:
        return f"<MediaAsset(id={self.id}, type={self.asset_type}, name={self.name})>"


class Collection(Base, TimestampMixin):
    """Collection model for grouping content."""
    
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
    cover_image_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    
    # Relationships
    contents: Mapped[list["ContentCollection"]] = relationship(
        "ContentCollection",
        back_populates="collection",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, name={self.name})>"


class ContentCollection(Base):
    """Association table for content in collections."""
    
    __tablename__ = "content_collections"
    
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        primary_key=True,
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="CASCADE"),
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
    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection",
        back_populates="contents",
    )
    content: Mapped["Content"] = relationship(
        "Content",
        back_populates="collections",
    )


class LearningPath(Base, TimestampMixin):
    """Learning path model for organizing sequential content."""
    
    __tablename__ = "learning_paths"
    __table_args__ = (
        Index("ix_learning_paths_title", "title"),
        Index("ix_learning_paths_owner_id", "owner_id"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    cover_image_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    target_education_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    estimated_duration_hours: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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
    contents: Mapped[list["LearningPathContent"]] = relationship(
        "LearningPathContent",
        back_populates="learning_path",
        cascade="all, delete-orphan",
        order_by="LearningPathContent.order_index",
    )
    
    def __repr__(self) -> str:
        return f"<LearningPath(id={self.id}, title={self.title})>"


class LearningPathContent(Base):
    """Association table for content in learning paths."""
    
    __tablename__ = "learning_path_contents"
    
    learning_path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        primary_key=True,
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    min_passing_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    learning_path: Mapped["LearningPath"] = relationship(
        "LearningPath",
        back_populates="contents",
    )
    content: Mapped["Content"] = relationship(
        "Content",
        back_populates="learning_paths",
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
    slug: Mapped[str] = mapped_column(
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
        nullable=False,
        default=0,
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    
    # Relationships
    contents: Mapped[list["Content"]] = relationship(
        "Content",
        back_populates="tags_relation",
    )
    
    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"
