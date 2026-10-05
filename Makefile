.PHONY: help build up down restart logs clean test unit-test demo validate

# Default target
help:
	@echo "🚀 RAGOPS - Retrieval-Augmented Generation Operations"
	@echo ""
	@echo "Available commands:"
	@echo "  build      - Build all Docker images"
	@echo "  up         - Start all services"
	@echo "  down       - Stop all services"
	@echo "  restart    - Restart all services"
	@echo "  logs       - Show service logs"
	@echo "  clean      - Clean up Docker resources"
	@echo "  test       - Run comprehensive test suite"
	@echo "  unit-test  - Run offline pytest suite (fake LLM/embeddings)"
	@echo "  demo       - Run feature demonstrations"
	@echo "  validate   - Validate Phase 2 functionality"
	@echo ""

build:
	@echo "🏗️  Building Docker images..."
	docker compose build

up:
	@echo "🚀 Starting RAGOPS services..."
	docker compose up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "✅ RAGOPS is ready!"
	@echo "   Backend: http://localhost:18000"
	@echo "   Health:  http://localhost:18000/health"

down:
	@echo "⏹️  Stopping RAGOPS services..."
	docker compose down

restart:
	@echo "🔄 Restarting RAGOPS services..."
	docker compose down
	docker compose up -d

logs:
	@echo "📄 Showing service logs..."
	docker compose logs -f backend

clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker compose down -v
	docker system prune -f

test:
	@echo "🧪 Running comprehensive test suite..."
	@python3 tests/test_phase2_comprehensive.py

unit-test:
	@echo "🧪 Running offline pytest suite..."
	pytest

# Development targets
dev-logs:
	docker compose logs -f

dev-rebuild:
	docker compose build --no-cache backend
	docker compose restart backend

dev-reset:
	docker compose down -v
	docker compose up -d
	@sleep 10
	curl -X POST "http://localhost:18000/init-index"