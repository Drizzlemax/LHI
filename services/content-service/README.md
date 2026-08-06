# PANDORA Content Service

Document storage and management service for the PANDORA learning platform.

## Features

- **Document Upload**: Upload documents (PDF, EPUB, DOC, TXT, HTML, Markdown)
- **S3 Storage**: Store documents in AWS S3 or compatible storage (MinIO)
- **Collections**: Organize documents into collections
- **Metadata**: Track content metadata (language, page count, word count)
- **Presigned URLs**: Generate secure upload/download URLs
- **Versioning**: Track document versions

## Architecture

```
┌─────────────────┐
│  API Gateway    │
└────────┬────────┘
         │
┌────────▼────────┐
│ Content Service │◄──── PostgreSQL
└────────┬────────┘
         │
┌────────▼────────┐
│  S3 / MinIO    │
└─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose

### Local Development

```bash
# Start dependencies
docker compose up -d postgres redis minio createbuckets

# Install dependencies
uv sync

# Run migrations
alembic upgrade head

# Run the service
uvicorn src.api.main:app --reload --port 8001
```

### Docker

```bash
# Build and run
docker compose up -d

# View logs
docker compose logs -f content-service
```

## API Endpoints

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |

### Content

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/content/upload` | Upload document |
| POST | `/api/v1/content/upload-url` | Get presigned upload URL |
| GET | `/api/v1/content/{id}` | Get document |
| PATCH | `/api/v1/content/{id}` | Update document |
| DELETE | `/api/v1/content/{id}` | Delete document |
| GET | `/api/v1/content/` | List documents |
| GET | `/api/v1/content/{id}/download` | Get download URL |

### Collections

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/collections/` | Create collection |
| GET | `/api/v1/collections/{id}` | Get collection |
| PATCH | `/api/v1/collections/{id}` | Update collection |
| DELETE | `/api/v1/collections/{id}` | Delete collection |
| GET | `/api/v1/collections/` | List collections |
| POST | `/api/v1/collections/{id}/documents/{doc_id}` | Add document |
| DELETE | `/api/v1/collections/{id}/documents/{doc_id}` | Remove document |

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/1` |
| `AWS_ACCESS_KEY_ID` | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - |
| `AWS_REGION` | AWS region | `us-east-1` |
| `S3_BUCKET_NAME` | S3 bucket name | `pandora-content` |
| `S3_ENDPOINT_URL` | S3 endpoint (for MinIO) | - |
| `STORAGE_BACKEND` | Storage type (`s3`, `minio`, `local`) | `s3` |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_content.py
```

## License

Apache 2.0
