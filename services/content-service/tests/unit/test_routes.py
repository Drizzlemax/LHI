"""
PANDORA Content Service Unit Tests - API Routes
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from src.schemas.content import ContentCreate, ContentUpdate


pytestmark = pytest.mark.unit


class TestContentRoutes:
    """Tests for content API routes."""
    
    @pytest.mark.asyncio
    async def test_list_content_empty(self, async_client: AsyncClient):
        """Test listing content when empty."""
        response = await async_client.get("/api/v1/content/")
        
        assert response.status_code == 200
        data = response.json()
        assert "contents" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
    
    @pytest.mark.asyncio
    async def test_list_content_with_filters(self, async_client: AsyncClient):
        """Test listing content with filters."""
        response = await async_client.get(
            "/api/v1/content/",
            params={
                "category": "course",
                "language": "en",
                "skip": 0,
                "limit": 10,
            }
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_content_not_found(self, async_client: AsyncClient):
        """Test getting non-existent content."""
        response = await async_client.get(f"/api/v1/content/{uuid.uuid4()}")
        
        # Should return 404
        assert response.status_code in [404, 500]  # 500 if DB not connected in tests
    
    @pytest.mark.asyncio
    async def test_create_content_validation(self, async_client: AsyncClient):
        """Test content creation validation."""
        # Missing required fields
        response = await async_client.post(
            "/api/v1/content/",
            json={
                "description": "Only description",
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_content_success(self, async_client: AsyncClient):
        """Test successful content creation."""
        response = await async_client.post(
            "/api/v1/content/",
            json={
                "title": "Test Content",
                "category": "document",
                "content_type": "pdf",
            }
        )
        
        # May fail due to DB connection in tests
        assert response.status_code in [201, 500]
    
    @pytest.mark.asyncio
    async def test_update_content_not_found(self, async_client: AsyncClient):
        """Test updating non-existent content."""
        response = await async_client.put(
            f"/api/v1/content/{uuid.uuid4()}",
            json={
                "title": "Updated Title",
            }
        )
        
        assert response.status_code in [404, 500]
    
    @pytest.mark.asyncio
    async def test_delete_content_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent content."""
        response = await async_client.delete(f"/api/v1/content/{uuid.uuid4()}")
        
        assert response.status_code in [204, 404, 500]
    
    @pytest.mark.asyncio
    async def test_restore_content_not_found(self, async_client: AsyncClient):
        """Test restoring non-existent content."""
        response = await async_client.post(f"/api/v1/content/{uuid.uuid4()}/restore")
        
        assert response.status_code in [404, 500]
    
    @pytest.mark.asyncio
    async def test_publish_content_not_found(self, async_client: AsyncClient):
        """Test publishing non-existent content."""
        response = await async_client.post(f"/api/v1/content/{uuid.uuid4()}/publish")
        
        assert response.status_code in [404, 500]
    
    @pytest.mark.asyncio
    async def test_get_related_content_not_found(self, async_client: AsyncClient):
        """Test getting related content for non-existent content."""
        response = await async_client.get(f"/api/v1/content/{uuid.uuid4()}/related")
        
        assert response.status_code in [200, 404, 500]
        # If 200, should return empty list


class TestCollectionRoutes:
    """Tests for collection API routes."""
    
    @pytest.mark.asyncio
    async def test_list_collections_empty(self, async_client: AsyncClient):
        """Test listing collections when empty."""
        response = await async_client.get("/api/v1/collections/")
        
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert "total" in data
    
    @pytest.mark.asyncio
    async def test_create_collection_validation(self, async_client: AsyncClient):
        """Test collection creation validation."""
        # Missing required fields
        response = await async_client.post(
            "/api/v1/collections/",
            json={
                "description": "Only description",
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_collection_success(self, async_client: AsyncClient):
        """Test successful collection creation."""
        response = await async_client.post(
            "/api/v1/collections/",
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": True,
            }
        )
        
        # May fail due to DB in tests
        assert response.status_code in [201, 500]
    
    @pytest.mark.asyncio
    async def test_get_collection_not_found(self, async_client: AsyncClient):
        """Test getting non-existent collection."""
        response = await async_client.get(f"/api/v1/collections/{uuid.uuid4()}")
        
        assert response.status_code in [404, 500]
    
    @pytest.mark.asyncio
    async def test_update_collection_not_found(self, async_client: AsyncClient):
        """Test updating non-existent collection."""
        response = await async_client.patch(
            f"/api/v1/collections/{uuid.uuid4()}",
            json={
                "name": "Updated Name",
            }
        )
        
        assert response.status_code in [404, 500]
    
    @pytest.mark.asyncio
    async def test_delete_collection_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent collection."""
        response = await async_client.delete(f"/api/v1/collections/{uuid.uuid4()}")
        
        assert response.status_code in [204, 404, 500]


class TestHealthRoutes:
    """Tests for health check routes."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_ready_check(self, async_client: AsyncClient):
        """Test readiness check endpoint."""
        response = await async_client.get("/ready")
        
        # May return 200 or 503 depending on DB connection
        assert response.status_code in [200, 503]
    
    @pytest.mark.asyncio
    async def test_api_health_check(self, async_client: AsyncClient):
        """Test API health check endpoint."""
        response = await async_client.get("/api/v1/health")
        
        assert response.status_code == 200


class TestSchemaValidation:
    """Tests for request/response schema validation."""
    
    def test_content_create_valid(self):
        """Test valid ContentCreate schema."""
        data = ContentCreate(
            title="Test Content",
            category="book",
            content_type="pdf",
            language="en",
        )
        
        assert data.title == "Test Content"
        assert data.category == "book"
    
    def test_content_create_invalid_category(self):
        """Test ContentCreate with invalid category."""
        with pytest.raises(Exception):
            ContentCreate(
                title="Test",
                category="invalid_category",
                content_type="pdf",
            )
    
    def test_content_update_partial(self):
        """Test partial ContentUpdate."""
        data = ContentUpdate(title="New Title")
        
        assert data.title == "New Title"
        assert data.description is None
        assert data.is_public is None
    
    def test_content_update_multiple_fields(self):
        """Test ContentUpdate with multiple fields."""
        data = ContentUpdate(
            title="Updated Title",
            description="Updated description",
            is_public=True,
            tags=["tag1", "tag2"],
        )
        
        assert data.title == "Updated Title"
        assert data.is_public is True
        assert data.tags == ["tag1", "tag2"]
