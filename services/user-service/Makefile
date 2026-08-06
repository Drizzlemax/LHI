# PANDORA User Service Makefile

.PHONY: help dev test lint format clean migrate db-shell docker-build docker-up docker-down

# Default target
help:
	@echo "PANDORA User Service - Available commands:"
	@echo ""
	@echo "  make dev          - Start development environment (docker)"
	@echo "  make test          - Run all tests"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make lint          - Run linter (ruff)"
	@echo "  make format        - Format code (ruff)"
	@echo "  make mypy          - Run type checker (mypy)"
	@echo "  make clean         - Clean up caches and build artifacts"
	@echo "  make migrate       - Run database migrations"
	@echo "  make db-shell      - Open PostgreSQL shell"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"
	@echo ""

# Development
dev:
	docker compose up -d
	@echo "Services started. Run 'make migrate' to set up the database."

# Testing
test:
	pytest --cov=src --cov-report=term-missing --cov-report=html

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v --tb=short

test-watch:
	pytest tests/unit -v --watch

# Code Quality
lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check src/ tests/ --fix

mypy:
	mypy src/

pre-commit:
	pre-commit run --all-files

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

# Database
migrate:
	alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	alembic revision --message="$$name"

migrate-rollback:
	alembic downgrade -1

migrate-status:
	alembic current

db-shell:
	docker compose exec postgres psql -U postgres -d pandora_users

db-reset:
	docker compose down -v
	docker compose up -d
	sleep 5
	make migrate

# Docker
docker-build:
	docker build -t pandora/user-service:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f user-service

docker-rebuild:
	docker compose up -d --build

# Run locally (without Docker)
run:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Generate coverage report
coverage:
	pytest --cov=src --cov-report=term-missing --cov-report=html
	open htmlcov/index.html 2>/dev/null || echo "Coverage report at htmlcov/index.html"

# Security scan
security:
	ruff check src/ --select=SEC
	bandit -r src/

# Dependency management
deps:
	uv sync

deps-update:
	uv pip compile pyproject.toml -o requirements.txt
	uv pip compile pyproject.toml -o requirements-dev.txt

# OpenAPI docs
docs:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
	sleep 3
	open http://localhost:8000/docs 2>/dev/null || echo "Docs at http://localhost:8000/docs"
