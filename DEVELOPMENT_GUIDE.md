# PANDORA Development Guide

**Version:** 1.0.0  
**Last Updated:** 2026-08-05

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Project Structure](#project-structure)
4. [Local Development](#local-development)
5. [Service Development](#service-development)
6. [Testing](#testing)
7. [Code Style](#code-style)
8. [Git Workflow](#git-workflow)
9. [Debugging](#debugging)
10. [Performance Profiling](#performance-profiling)

---

## Getting Started

### Prerequisites

- **Python** 3.12+
- **Node.js** 20+
- **Docker** 24+
- **Docker Compose** 2.20+
- **kubectl** 1.28+
- **helm** 3.12+
- **Terraform** 1.6+
- **Git** 2.40+

### Quick Start

```bash
# Clone the repository
git clone https://github.com/pandora/platform.git
cd pandora

# Copy environment template
cp .env.example .env

# Start all services
make dev-up

# Run migrations
make migrate

# Seed development data
make seed-dev

# Open browser
open http://localhost:3000
```

---

## Development Environment

### Environment Variables

```bash
# .env file structure
# ===================

# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=debug

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pandora
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Vector Database
VECTOR_DB_URL=http://localhost:6333
VECTOR_DB_API_KEY=dev-key

# Knowledge Graph
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Elasticsearch
ES_URL=http://localhost:9200
ES_USER=elastic
ES_PASSWORD=password

# Kafka
KAFKA_BROKER_URL=localhost:9092
KAFKA_CONSUMER_GROUP=pandora-dev

# Authentication
JWT_SECRET=dev-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

# AI Services
LLM_PROVIDER=vllm
LLM_BASE_URL=http://localhost:8000/v1
LLM_API_KEY=dev-key
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
RERANKER_MODEL=BAAI/bge-reranker-large

# Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=pandora

# External Services
CLOUDFLARE_API_KEY=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Monitoring
SENTRY_DSN=
PROMETHEUS_ENABLED=true
JAEGER_ENABLED=true
```

### IDE Setup

#### VS Code

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting Ruff.enabled": true,
  "python.formatting.provider": "ruff",
  "python.testing.pytestEnabled": true,
  "python.analysis.typeCheckingMode": "basic",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fix.all": true
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.codeActionsOnSave": {
      "source.fix.all": true
    }
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/node_modules": true
  }
}
```

#### Recommended Extensions

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylint",
    "charliermarsh.ruff",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "graphql.vscode-graphql",
    "ms-azuretools.vscode-docker",
    "ms-vscode-remote.remote-containers",
    "ms-vscode-remote.remote-ssh",
    "ms-kubernetes-tools.vscode-kubernetes-tools"
  ]
}
```

---

## Project Structure

### Monorepo Layout

```
pandora/
├── services/                 # Backend microservices
│   ├── api-gateway/         # Kong/API Gateway
│   ├── user-service/        # User management
│   ├── content-service/     # Content management
│   ├── search-service/      # Search & discovery
│   ├── learning-service/    # Learning paths & progress
│   ├── quiz-service/        # Assessments
│   ├── recommendation-service/
│   ├── ai-gateway/          # AI orchestration
│   └── crawler-service/     # Content ingestion
│
├── shared/                   # Shared libraries
│   ├── models/             # Pydantic models
│   ├── utils/              # Utilities
│   ├── constants/          # Constants
│   └── exceptions/         # Custom exceptions
│
├── ml/                      # ML models
│   ├── embeddings/
│   ├── reranker/
│   ├── curriculum/
│   └── recommendation/
│
├── web/                     # Next.js frontend
│   ├── src/
│   │   ├── app/           # Pages
│   │   ├── components/    # React components
│   │   ├── lib/          # Utilities
│   │   ├── hooks/        # Custom hooks
│   │   ├── stores/       # State management
│   │   └── styles/       # Global styles
│   └── tests/
│
├── infrastructure/         # IaC
│   ├── terraform/
│   └── kubernetes/
│
├── scripts/                # Dev scripts
│
└── docs/                  # Documentation
```

---

## Local Development

### Docker Compose Setup

```yaml
# docker-compose.dev.yml
version: '3.9'

services:
  # Database
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: pandora
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

  # Knowledge Graph
  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

  # Search
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=password
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  # Cache & Queue
  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  # Object Storage
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./infrastructure/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "4317:4317"
      - "4318:4318"

volumes:
  postgres_data:
  qdrant_data:
  neo4j_data:
  es_data:
  redis_data:
  minio_data:
```

### Makefile Commands

```makefile
# Makefile

.PHONY: help dev-up dev-down dev-logs migrate seed-dev test lint format clean

# Development
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev-up: ## Start all services
	docker compose -f docker-compose.dev.yml up -d
	@echo "Waiting for services..."
	@sleep 5
	@docker compose -f docker-compose.dev.yml ps

dev-down: ## Stop all services
	docker compose -f docker-compose.dev.yml down

dev-logs: ## Show logs
	docker compose -f docker-compose.dev.yml logs -f

# Database
migrate: ## Run migrations
	cd services/user-service && alembic upgrade head

seed-dev: ## Seed development data
	python scripts/seed_data.py --env=dev

# Testing
test: ## Run all tests
	pytest --cov=services --cov-report=html

test-unit: ## Run unit tests
	pytest tests/unit -v

test-integration: ## Run integration tests
	pytest tests/integration -v --tb=short

test-e2e: ## Run e2e tests
	playwright test

# Code Quality
lint: ## Run linters
	ruff check .
	eslint web/src --ext .ts,.tsx
	tflint infrastructure/terraform

format: ## Format code
	ruff format .
	prettier --write .
	docker run --rm -v $(pwd):/app mabenj/ansible-lint ansible/

# Cleanup
clean: ## Clean up containers and volumes
	docker compose -f docker-compose.dev.yml down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```

---

## Service Development

### Creating a New Service

```bash
# 1. Create service directory
mkdir -p services/my-new-service/src

# 2. Create project structure
cd services/my-new-service
mkdir -p src/api src/core src/models src/services tests

# 3. Initialize Python project
cat > pyproject.toml << EOF
[project]
name = "pandora-my-new-service"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.109.0",
    "pydantic>=2.5.0",
    "shared@file:../../shared",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.26.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
EOF

# 4. Create Dockerfile
cat > Dockerfile << EOF
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# 5. Create main app
cat > src/api/main.py << EOF
from fastapi import FastAPI
from shared.models import BaseModel

app = FastAPI(title="My New Service")

class HealthResponse(BaseModel):
    status: str

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy")
EOF

# 6. Add to docker-compose
echo """
  my-new-service:
    build: ./services/my-new-service
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=\${DATABASE_URL}
      - REDIS_URL=\${REDIS_URL}
    depends_on:
      - postgres
      - redis
""" >> docker-compose.dev.yml
```

### Service Template

```python
# services/my-new-service/src/api/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from src.api.routes import router as api_router
from src.core.config import settings
from src.core.database import init_db, close_db
from src.core.logging import setup_logging

tracer = trace.get_tracer(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="PANDORA My New Service",
    version="1.0.0",
    description="Service description",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router, prefix="/api/v1")

# Instrumentation
FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "my-new-service"}
```

### Service Communication

#### Synchronous (HTTP)

```python
# Using HTTPX for service-to-service communication
import httpx

class UserServiceClient:
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_user(self, user_id: str) -> dict:
        response = await self.client.get(f"{self.base_url}/users/{user_id}")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()
```

#### Asynchronous (Kafka)

```python
# Kafka producer
from aiokafka import AIOKafkaProducer
import json

class EventProducer:
    def __init__(self):
        self.producer = None
    
    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKER_URL,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )
        await self.producer.start()
    
    async def emit(self, topic: str, event: dict, key: str = None):
        await self.producer.send_and_wait(
            topic, 
            value=event,
            key=key.encode('utf-8') if key else None,
        )
    
    async def stop(self):
        await self.producer.stop()

# Kafka consumer
from aiokafka import AIOKafkaConsumer

class EventConsumer:
    def __init__(self, topic: str, group_id: str):
        self.topic = topic
        self.consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BROKER_URL,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        )
    
    async def start(self):
        await self.consumer.start()
    
    async def consume(self):
        async for msg in self.consumer:
            yield msg.value
    
    async def stop(self):
        await self.consumer.stop()
```

---

## Testing

### Test Structure

```
tests/
├── unit/
│   ├── services/
│   │   ├── test_user_service.py
│   │   └── test_content_service.py
│   ├── models/
│   │   └── test_models.py
│   └── utils/
│       └── test_utils.py
├── integration/
│   ├── api/
│   │   ├── test_auth.py
│   │   └── test_users.py
│   └── services/
│       └── test_kafka.py
├── fixtures/
│   ├── factories.py
│   └── conftest.py
└── e2e/
    ├── login.spec.ts
    └── learning_path.spec.ts
```

### Pytest Configuration

```python
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=services
    --cov-report=html
    --cov-report=term-missing
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Test Examples

```python
# tests/unit/services/test_user_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.user_service import UserService
from src.models.user import UserCreate, UserResponse


class TestUserService:
    
    @pytest.fixture
    def user_repo(self):
        return AsyncMock()
    
    @pytest.fixture
    def user_service(self, user_repo):
        return UserService(user_repository=user_repo)
    
    @pytest.mark.unit
    async def test_create_user_success(self, user_service, user_repo):
        # Arrange
        user_data = UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        user_repo.create.return_value = UserResponse(
            id="uuid-123",
            email=user_data.email,
            full_name=user_data.full_name,
        )
        
        # Act
        result = await user_service.create_user(user_data)
        
        # Assert
        assert result.email == user_data.email
        assert result.full_name == user_data.full_name
        user_repo.create.assert_called_once()
    
    @pytest.mark.unit
    async def test_create_user_duplicate_email(self, user_service, user_repo):
        # Arrange
        user_data = UserCreate(
            email="existing@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        user_repo.get_by_email.return_value = {"id": "existing"}
        
        # Act & Assert
        with pytest.raises(DuplicateEmailError):
            await user_service.create_user(user_data)
```

```python
# tests/integration/api/test_auth.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app


class TestAuthEndpoints:
    
    @pytest.mark.integration
    async def test_login_success(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.integration
    async def test_login_invalid_credentials(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
```

---

## Code Style

### Python (Ruff Configuration)

```toml
# ruff.toml
line-length = 100
target-version = "py312"

[lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # Pyflakes
    "I",     # isort
    "UP",    # pyupgrade
    "B",     # flake8-bugbear
    "C4",    # flake8-comprehensions
    "DTZ",   # flake8-datetimez
    "T10",   # flake8-debugger
    "ISC",   # flake8-implicit-str-concat
    "PIE",   # flake8-pie
    "RET",   # flake8-return
    "SIM",   # flake8-simplify
    "TCH",   # flake8-type-checking
    "RUF",   # Ruff-specific rules
]
ignore = [
    "E501",   # line too long (handled by formatter)
    "ISC001", # may cause conflicts with formatter
]

[lint.isort]
known-first-party = ["src"]
force-single-line = false
```

### TypeScript/JavaScript (ESLint + Prettier)

```javascript
// web/.eslintrc.js
module.exports = {
  extends: [
    'next/core-web-vitals',
    'plugin:@typescript-eslint/recommended-type-checked',
    'prettier',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    project: './tsconfig.json',
    tsconfigRootDir: __dirname,
  },
  plugins: ['@typescript-eslint', 'unused-imports'],
  rules: {
    '@typescript-eslint/no-unused-vars': 'off',
    'unused-imports/no-unused-imports': 'error',
    '@typescript-eslint/no-misused-promises': [
      'error',
      { checksVoidReturn: false },
    ],
  },
};
```

```javascript
// web/.prettierrc.js
module.exports = {
  semi: true,
  singleQuote: true,
  trailingComma: 'es5',
  printWidth: 100,
  tabWidth: 2,
  useTabs: false,
  arrowParens: 'always',
  endOfLine: 'lf',
};
```

---

## Git Workflow

### Branch Naming

```
feature/add-curriculum-generator
bugfix/fix-search-latency
hotfix/security-patch-auth
refactor/improve-api-response-times
docs/update-api-documentation
```

### Commit Messages

```bash
# Format
<type>(<scope>): <description>

# Types
# feat: New feature
# fix: Bug fix
# docs: Documentation changes
# style: Code style changes (formatting)
# refactor: Code refactoring
# perf: Performance improvements
# test: Adding or updating tests
# chore: Build process or auxiliary tool changes

# Examples
feat(search): add hybrid search with vector similarity
fix(auth): resolve token refresh race condition
docs(api): update OpenAPI specification
refactor(content): extract content validation logic
perf(embeddings): optimize batch processing
test(quiz): add integration tests for adaptive assessment
```

### Pull Request Process

```markdown
## Description
<!-- What does this PR do? -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No console warnings/errors

## Screenshots (if applicable)

## Related Issues
Closes #123
```

---

## Debugging

### Python Debugging

```bash
# Debug with VS Code
# .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "services.user-service.src.api.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "cwd": "${workspaceFolder}",
      "env": {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/pandora",
        "DEBUG": "1"
      }
    }
  ]
}
```

### Logging Best Practices

```python
import structlog
from opentelemetry import trace

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

# Usage
logger = structlog.get_logger()

async def my_function(user_id: str):
    logger.info(
        "processing_user",
        user_id=user_id,
        trace_id=trace.get_current_span().context.trace_id,
    )
```

---

## Performance Profiling

### Python Profiling

```bash
# Memory profiling
pip install memory_profiler
python -m memory_profiler src/slow_function.py

# CPU profiling
pip install py-spy
py-spy record -o profile.svg --pid $(pgrep -f uvicorn)

# Line profiler
pip install line_profiler
kernprof -l -v src/function_to_profile.py
```

### API Performance Testing

```bash
# Using k6
# scripts/load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('http://localhost:8000/api/v1/search?q=test');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'has results': (r) => JSON.parse(r.body).results?.length > 0,
  });
  sleep(1);
}
```

```bash
# Run load test
k6 run scripts/load-test.js
```

---

## Appendix: Useful Commands

```bash
# View all running containers
docker compose -f docker-compose.dev.yml ps

# Access PostgreSQL
docker exec -it pandora-postgres-1 psql -U postgres -d pandora

# Access Redis
docker exec -it pandora-redis-1 redis-cli

# View logs for specific service
docker compose -f docker-compose.dev.yml logs -f user-service

# Restart a service
docker compose -f docker-compose.dev.yml restart user-service

# Rebuild service
docker compose -f docker-compose.dev.yml up -d --build user-service

# Shell into running container
docker exec -it pandora-user-service-1 /bin/sh

# View resource usage
docker stats

# Clean up everything
docker compose -f docker-compose.dev.yml down -v --rmi all
```

---

*Last updated: 2026-08-05*
