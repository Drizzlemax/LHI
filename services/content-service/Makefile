# PANDORA Content Service Makefile

.PHONY: help dev test lint format clean migrate docker-build docker-up docker-down

help:
	@echo "PANDORA Content Service - Available commands:"
	@echo ""
	@echo "  make dev          - Start development environment (docker)"
	@echo "  make test          - Run all tests"
	@echo "  make lint          - Run linter (ruff)"
	@echo "  make format        - Format code (ruff)"
	@echo "  make clean         - Clean up caches"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"

dev:
	docker compose up -d
	@echo "Services started. Run 'make migrate' to set up the database."

test:
	pytest --cov=src --cov-report=term-missing --cov-report=html

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check src/ tests/ --fix

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .coverage

docker-build:
	docker build -t pandora/content-service:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

run:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001
