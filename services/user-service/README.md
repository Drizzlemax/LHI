# PANDORA User Service

Authentication and user management service for the PANDORA learning platform.

## Features

- User registration and authentication
- JWT-based authentication with access/refresh tokens
- Multi-Factor Authentication (TOTP)
- Learning profile management
- User preferences
- Session management with Redis

## Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0 (async)
- **Cache**: Redis 7.2
- **Auth**: JWT (python-jose) with bcrypt password hashing
- **Observability**: OpenTelemetry, structured logging

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16
- Redis 7.2

### Installation

```bash
# Install dependencies
uv sync

# Run database migrations
alembic upgrade head

# Start the service
uvicorn src.api.main:app --reload
```

### Docker

```bash
# Start all dependencies
docker compose up -d

# Run migrations
docker compose exec user-service alembic upgrade head

# View logs
docker compose logs -f user-service
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login user |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout user |
| POST | `/api/v1/auth/mfa/setup` | Setup MFA |
| POST | `/api/v1/auth/mfa/verify` | Verify MFA code |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user profile |
| PATCH | `/api/v1/users/me` | Update current user profile |
| GET | `/api/v1/users/me/learning-profile` | Get learning profile |
| PUT | `/api/v1/users/me/learning-profile` | Update learning profile |
| GET | `/api/v1/users/me/preferences` | Get user preferences |
| PATCH | `/api/v1/users/me/preferences` | Update user preferences |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy src/
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | postgresql+asyncpg://... |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |
| `JWT_SECRET_KEY` | Secret key for JWT signing | changeme |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | 15 |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | 7 |

## Project Structure

```
user-service/
├── src/
│   ├── api/
│   │   ├── main.py          # FastAPI application
│   │   └── routes/         # API route handlers
│   ├── core/
│   │   ├── config.py       # Settings and configuration
│   │   ├── security.py     # Auth utilities
│   │   └── logging.py      # Structured logging
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   └── repositories/      # Data access layer
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/       # Integration tests
├── alembic/              # Database migrations
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

Apache 2.0
