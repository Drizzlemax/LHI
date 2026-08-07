"""
PANDORA Content Service Test Fixtures
"""
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.models.content import (
    Content,
    ContentMetadata,
    ContentStatus,
    ContentCategory,
)
from src.core.database import get_db
from src.api.main import app


# Test database URL (SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory database session for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    
    # Import and create tables
    from src.models.base import Base
    from src.models.content import (
        Content,
        ContentMetadata,
        ContentVector,
        ContentVersion,
        MediaAsset,
        Collection,
        ContentCollection,
        LearningPath,
        LearningPathContent,
        Tag,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with session_factory() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    return session


@pytest.fixture
def sample_content_id() -> uuid.UUID:
    """Generate a sample content ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_owner_id() -> uuid.UUID:
    """Generate a sample owner ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_content_data(sample_content_id: uuid.UUID, sample_owner_id: uuid.UUID) -> dict:
    """Sample content creation data."""
    return {
        "title": "Introduction to Machine Learning",
        "description": "A comprehensive guide to ML fundamentals",
        "summary": "Learn the basics of machine learning",
        "category": ContentCategory.COURSE.value,
        "content_type": "pdf",
        "education_level": "undergraduate",
        "language": "en",
        "file_size": 1024000,
        "storage_key": f"content/{sample_content_id}/file.pdf",
        "checksum": "abc123def456",
        "status": ContentStatus.DRAFT.value,
        "is_public": False,
        "is_featured": False,
        "is_premium": True,
        "owner_id": sample_owner_id,
        "tags": ["machine-learning", "python", "ai"],
        "metadata": {"difficulty": "beginner"},
    }


@pytest.fixture
def sample_content(sample_content_id: uuid.UUID, sample_owner_id: uuid.UUID) -> Content:
    """Create a sample Content model instance."""
    content = Content(
        id=sample_content_id,
        title="Introduction to Machine Learning",
        description="A comprehensive guide to ML fundamentals",
        summary="Learn the basics of machine learning",
        category=ContentCategory.COURSE.value,
        content_type="pdf",
        education_level="undergraduate",
        language="en",
        file_size=1024000,
        storage_key=f"content/{sample_content_id}/file.pdf",
        checksum="abc123def456",
        status=ContentStatus.DRAFT.value,
        is_public=False,
        is_featured=False,
        is_premium=True,
        owner_id=sample_owner_id,
        tags=["machine-learning", "python", "ai"],
        metadata={"difficulty": "beginner"},
    )
    # Set timestamps
    now = datetime.now(timezone.utc)
    content.created_at = now
    content.updated_at = now
    return content


@pytest.fixture
def sample_content_metadata(sample_content_id: uuid.UUID) -> ContentMetadata:
    """Create a sample ContentMetadata model instance."""
    metadata = ContentMetadata(
        id=uuid.uuid4(),
        content_id=sample_content_id,
        authors=["John Doe", "Jane Smith"],
        publication_date=datetime(2023, 1, 15, tzinfo=timezone.utc),
        publication_year=2023,
        publisher="PANDORA Press",
        isbn="978-0-123456-78-9",
        subjects=["Computer Science", "Artificial Intelligence"],
        keywords=["machine learning", "data science"],
        average_rating=4.5,
        rating_count=128,
        view_count=1542,
        download_count=342,
    )
    now = datetime.now(timezone.utc)
    metadata.created_at = now
    metadata.updated_at = now
    return metadata


@pytest.fixture
def sample_collection_id() -> uuid.UUID:
    """Generate a sample collection ID."""
    return uuid.uuid4()


@pytest.fixture
def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    
    yield client
    
    client.close()
    app.dependency_overrides.clear()


@pytest.fixture
def mock_storage():
    """Create a mock storage backend."""
    storage = MagicMock()
    storage.generate_storage_key = MagicMock(return_value="content/test-id/file.pdf")
    storage.generate_upload_url = MagicMock(return_value="https://s3.example.com/upload")
    storage.generate_download_url = MagicMock(return_value="https://s3.example.com/download")
    storage.upload_file = AsyncMock(return_value=True)
    storage.delete_file = AsyncMock(return_value=True)
    storage.file_exists = AsyncMock(return_value=True)
    return storage


# ============ Search Fixtures ============

@pytest.fixture
def sample_search_filters():
    """Create sample search filters."""
    from src.search.query_builder import SearchFilters
    return SearchFilters(
        query="machine learning",
        category="course",
        education_level="undergraduate",
        language="en",
        is_public=True,
        tags=["ai", "ml"],
    )


@pytest.fixture
def sample_search_result():
    """Create sample search result."""
    from src.search.query_builder import SearchResult
    return SearchResult(
        total=100,
        hits=[
            {
                "id": "content-1",
                "score": 0.95,
                "source": {
                    "id": "content-1",
                    "title": "Machine Learning Basics",
                    "description": "Learn ML fundamentals",
                    "category": "course",
                },
                "highlight": {
                    "title": ["<mark>Machine</mark> <mark>Learning</mark> Basics"],
                },
            },
            {
                "id": "content-2",
                "score": 0.85,
                "source": {
                    "id": "content-2",
                    "title": "Advanced ML Techniques",
                    "description": "Advanced machine learning",
                    "category": "course",
                },
            },
        ],
        aggregations={
            "categories": {
                "buckets": [
                    {"key": "course", "doc_count": 50},
                    {"key": "book", "doc_count": 30},
                ]
            },
            "education_levels": {
                "buckets": [
                    {"key": "undergraduate", "doc_count": 60},
                    {"key": "graduate", "doc_count": 40},
                ]
            },
        },
        took_ms=25,
    )


@pytest.fixture
def sample_vector() -> list:
    """Create a sample embedding vector."""
    return [0.1, 0.2, 0.3, 0.4, 0.5, -0.1, -0.2, -0.3]


@pytest.fixture
def sample_vectors() -> list:
    """Create sample vectors for search testing."""
    return [
        {
            "id": "vec-1",
            "embedding": [0.9, 0.1, 0.2, 0.3, 0.4, -0.1, -0.2, -0.3],
            "source": {"title": "Vector 1", "category": "science"},
        },
        {
            "id": "vec-2",
            "embedding": [0.8, 0.2, 0.3, 0.4, 0.5, -0.2, -0.3, -0.4],
            "source": {"title": "Vector 2", "category": "science"},
        },
        {
            "id": "vec-3",
            "embedding": [0.1, 0.9, 0.1, 0.2, 0.3, -0.1, -0.2, -0.3],
            "source": {"title": "Vector 3", "category": "art"},
        },
    ]


@pytest.fixture
def mock_es_client() -> MagicMock:
    """Create a mock Elasticsearch client."""
    client = MagicMock()
    client.info = AsyncMock(return_value={
        "cluster_name": "test-cluster",
        "version": {"number": "8.12.0"},
    })
    client.cluster = MagicMock()
    client.cluster.health = AsyncMock(return_value={
        "status": "green",
        "cluster_name": "test-cluster",
        "number_of_nodes": 1,
        "active_shards": 5,
    })
    client.indices = MagicMock()
    client.indices.exists = AsyncMock(return_value=True)
    client.indices.create = AsyncMock()
    client.indices.delete = AsyncMock()
    client.indices.refresh = AsyncMock()
    client.search = AsyncMock(return_value={
        "hits": {
            "total": {"value": 2},
            "hits": [
                {"_id": "1", "_score": 0.95, "_source": {"title": "Test 1"}},
                {"_id": "2", "_score": 0.85, "_source": {"title": "Test 2"}},
            ],
        },
        "aggregations": {},
    })
    client.index = AsyncMock()
    client.get = AsyncMock(return_value={"_source": {"title": "Test"}})
    client.delete = AsyncMock()
    client.update = AsyncMock()
    client.close = AsyncMock()
    return client
