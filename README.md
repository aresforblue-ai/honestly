# Honestly - Truth Engine & Personal Proof Vault

A comprehensive blockchain-verified identity and credential verification system with zero-knowledge proofs and distributed trust infrastructure.

## 🏗️ Architecture

The Honestly platform consists of three main components:

### 1. **Frontend Application** (`frontend-app/`)
- React + Vite application
- TailwindCSS for styling
- Apollo Client for GraphQL
- AppWhistler UI for app verification

### 2. **GraphQL Backend** (`backend-graphql/`)
- Node.js + Apollo Server
- App verification and scoring engine
- Claims, evidence, and verdict management
- WhistlerScore calculation

### 3. **Python Backend** (`backend-python/`)
- FastAPI REST API
- Neo4j graph database
- Kafka event streaming
- FAISS vector search
- Hyperledger Fabric blockchain
- Zero-knowledge proof generation

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Docker & Docker Compose
- PostgreSQL (for GraphQL backend)
- Neo4j (for Python backend)

### 1. Start Infrastructure

```bash
docker-compose up -d
```

This starts:
- Neo4j (ports 7474, 7687)
- Kafka + Zookeeper (port 9092)
- PostgreSQL (port 5432)

### 2. Start Python Backend

```bash
cd backend-python
pip install -r requirements.txt
uvicorn api.app:app --reload
```

Access at: http://localhost:8000

### 3. Start GraphQL Backend

```bash
cd backend-graphql
npm install
npm run dev
```

Access at: http://localhost:4000/graphql

### 4. Start Frontend

```bash
cd frontend-app
npm install
npm run dev
```

Access at: http://localhost:3000

## 📚 Documentation

- [Vault API Documentation](docs/vault-api.md)
- [Vault Quick Start Guide](docs/vault-quickstart.md)
- [Personal Proof Vault Overview](docs/personal-proof-vault.md)
- [Project Scope](docs/Scope.md)

## 🔑 Features

### AppWhistler (GraphQL Backend)
- ✅ App verification and trust scoring
- ✅ Claims and evidence management
- ✅ Verdict tracking and provenance
- ✅ Multi-signal scoring engine
- ✅ Privacy, financial, and sentiment analysis

### Personal Proof Vault (Python Backend)
- ✅ Encrypted document storage (AES-256-GCM)
- ✅ Zero-knowledge proofs for selective disclosure
- ✅ Hyperledger Fabric attestations
- ✅ QR code generation for sharing
- ✅ Complete audit timeline
- ✅ Graph-based claim verification

## 🛠️ Development

### Testing

Frontend:
```bash
cd frontend-app
npm test
```

GraphQL Backend:
```bash
cd backend-graphql
npm test
```

Python Backend:
```bash
cd backend-python
pytest
```

### Linting

```bash
# Frontend
cd frontend-app && npm run lint

# GraphQL Backend
cd backend-graphql && npm run lint
```

## 📦 Project Structure

```
honestly/
├── frontend-app/           # React frontend application
│   ├── src/
│   │   ├── App.jsx        # Main application component
│   │   ├── main.jsx       # Application entry point
│   │   └── index.css      # Global styles
│   ├── package.json
│   └── vite.config.js
│
├── backend-graphql/        # Node.js GraphQL backend
│   ├── src/
│   │   ├── config/        # Configuration files
│   │   ├── graphql/       # Schema and resolvers
│   │   ├── loaders/       # Express and Apollo setup
│   │   └── utils/         # Utility functions
│   └── package.json
│
├── backend-python/         # Python FastAPI backend
│   ├── api/               # FastAPI routes
│   ├── vault/             # Vault implementation
│   ├── ingestion/         # Kafka integration
│   ├── blockchain/        # Fabric integration
│   └── vector_index/      # FAISS search
│
├── docs/                   # Documentation
├── neo4j/                  # Neo4j initialization
└── docker-compose.yml      # Infrastructure setup
```

## 🔐 Security Notes

**⚠️ MVP Warning:** This is a development MVP. For production:
- Implement proper JWT authentication
- Use production Fabric network
- Integrate real ZK-SNARK circuits
- Add rate limiting and security auditing
- Implement proper key management
- Enable HTTPS/TLS
- Add input sanitization

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions, please use the GitHub issue tracker.
