.PHONY: help install up down clean dev-frontend dev-backend-gql dev-backend-py

help:
	@echo "Honestly - Truth Engine & Personal Proof Vault"
	@echo ""
	@echo "Available commands:"
	@echo "  make install         - Install all dependencies"
	@echo "  make up              - Start infrastructure (Docker)"
	@echo "  make up-min          - Start minimal stack (API+Neo4j+frontend)"
	@echo "  make down            - Stop infrastructure"
	@echo "  make dev-frontend    - Start frontend development server"
	@echo "  make dev-backend-gql - Start GraphQL backend development server"
	@echo "  make dev-backend-py  - Start Python backend development server"
	@echo "  make clean           - Clean all build artifacts"
	@echo "  make test            - Run all tests"
	@echo "  make zkp-build       - Build zk circuits, zkeys, and vkeys"
	@echo "  make zkp-verify      - Verify sample proofs"
	@echo "  make perf-k6         - Run k6 load test (set BASE_URL, AUTH)"
	@echo "  make sbom            - Generate SBOM (trivy if available)"
	@echo "  make scan            - Dependency/FS scan (trivy/npm audit/pip-audit if available)"

install:
	@echo "Installing frontend dependencies..."
	cd frontend-app && npm install
	@echo "Installing GraphQL backend dependencies..."
	cd backend-graphql && npm install
	@echo "Installing Python backend dependencies..."
	cd backend-python && pip install -r requirements.txt

up:
	docker-compose -f docker-compose-updated.yml up -d

up-min:
	docker compose -f docker-compose.min.yml up --build

zkp-build:
	cd backend-python/zkp && npm install && \
	curl -L https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_16.ptau -o artifacts/common/pot16_final.ptau && \
	npx circom circuits/age.circom --r1cs --wasm --sym -o artifacts/age && \
	npx circom circuits/authenticity.circom --r1cs --wasm --sym -o artifacts/authenticity && \
	npx snarkjs groth16 setup artifacts/age/age.r1cs artifacts/common/pot16_final.ptau artifacts/age/age_0000.zkey && \
	npx snarkjs zkey contribute artifacts/age/age_0000.zkey artifacts/age/age_final.zkey -n "local" && \
	npx snarkjs zkey export verificationkey artifacts/age/age_final.zkey artifacts/age/verification_key.json && \
	npx snarkjs groth16 setup artifacts/authenticity/authenticity.r1cs artifacts/common/pot16_final.ptau artifacts/authenticity/authenticity_0000.zkey && \
	npx snarkjs zkey contribute artifacts/authenticity/authenticity_0000.zkey artifacts/authenticity/authenticity_final.zkey -n "local" && \
	npx snarkjs zkey export verificationkey artifacts/authenticity/authenticity_final.zkey artifacts/authenticity/verification_key.json

zkp-verify:
	cd backend-python/zkp && \
	node snark-runner.js prove age --input-file ./samples/age-input.sample.json > ./samples/age-proof.sample.json && \
	node snark-runner.js verify age --proof-file ./samples/age-proof.sample.json && \
	node snark-runner.js prove authenticity --input-file ./samples/authenticity-input.sample.json > ./samples/authenticity-proof.sample.json && \
	node snark-runner.js verify authenticity --proof-file ./samples/authenticity-proof.sample.json

perf-k6:
	@if ! command -v k6 >/dev/null 2>&1; then echo "k6 not installed. See https://k6.io/docs/get-started/installation/"; exit 1; fi
	BASE_URL=$${BASE_URL:-http://localhost:8000} AUTH=$${AUTH:-} k6 run tests/perf/k6-load.js

sbom:
	@if command -v trivy >/dev/null 2>&1; then trivy sbom --output sbom.json .; else echo "trivy not installed; skip SBOM (see https://trivy.dev)"; fi

scan:
	@if command -v trivy >/dev/null 2>&1; then trivy fs --severity CRITICAL,HIGH --exit-code 1 . || true; else echo "trivy not installed; skipping trivy scan"; fi
	@if command -v npm >/dev/null 2>&1; then cd frontend-app && npm audit --production || true; fi
	@if command -v npm >/dev/null 2>&1; then cd backend-graphql && npm audit --production || true; fi
	@if command -v pip-audit >/dev/null 2>&1; then pip-audit || true; else echo "pip-audit not installed; skipping"; fi

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
