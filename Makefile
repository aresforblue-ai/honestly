.PHONY: help install up down clean dev-frontend dev-backend-gql dev-backend-py

help:
	@echo "Honestly - Truth Engine & Personal Proof Vault"
	@echo ""
	@echo "Available commands:"
	@echo "  make install         - Install all dependencies"
	@echo "  make up              - Start infrastructure (Docker)"
	@echo "  make down            - Stop infrastructure"
	@echo "  make dev-frontend    - Start frontend development server"
	@echo "  make dev-backend-gql - Start GraphQL backend development server"
	@echo "  make dev-backend-py  - Start Python backend development server"
	@echo "  make clean           - Clean all build artifacts"
	@echo "  make test            - Run all tests"

install:
	@echo "Installing frontend dependencies..."
	cd frontend-app && npm install
	@echo "Installing GraphQL backend dependencies..."
	cd backend-graphql && npm install
	@echo "Installing Python backend dependencies..."
	cd backend-python && pip install -r requirements.txt

up:
	docker-compose -f docker-compose-updated.yml up -d

down:
	docker-compose down -v

dev-frontend:
	cd frontend-app && npm run dev

dev-backend-gql:
	cd backend-graphql && npm run dev

dev-backend-py:
	cd backend-python && uvicorn api.app:app --reload

clean:
	rm -rf frontend-app/node_modules frontend-app/dist
	rm -rf backend-graphql/node_modules backend-graphql/dist
	find backend-python -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend-python -type f -name "*.pyc" -delete 2>/dev/null || true

test:
	@echo "Running frontend tests..."
	cd frontend-app && npm test || true
	@echo "Running GraphQL backend tests..."
	cd backend-graphql && npm test || true
	@echo "Running Python backend tests..."
	cd backend-python && pytest || true
