# Honestly - Complete Setup Guide

This guide will help you set up the complete Honestly Truth Engine platform with all three components.

## 📋 Prerequisites

### Required Software
- **Node.js** 18.x or higher ([Download](https://nodejs.org/))
- **Python** 3.10 or higher ([Download](https://python.org/))
- **Docker** and **Docker Compose** ([Download](https://docker.com/))
- **Git** ([Download](https://git-scm.com/))

### Optional but Recommended
- **PostgreSQL** 16+ (or use Docker)
- **Neo4j** 5.x (or use Docker)

## 🚀 Quick Start (All Components)

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/aresforblue-ai/honestly.git
cd honestly

# Install all dependencies
make install
```

### Step 2: Start Infrastructure

```bash
# Start Docker services (Neo4j, Kafka, PostgreSQL)
make up

# Wait for services to be ready (about 30 seconds)
sleep 30
```

### Step 3: Initialize Databases

```bash
# Initialize Neo4j schema
docker exec honestly-neo4j cypher-shell -u neo4j -p test < neo4j/init.cypher
docker exec honestly-neo4j cypher-shell -u neo4j -p test < neo4j/vault_init.cypher

# (Optional) Initialize PostgreSQL for GraphQL backend
# If using Prisma:
cd backend-graphql
npm run prisma:migrate
cd ..
```

### Step 4: Configure Environment

```bash
# Frontend
cp frontend-app/.env.example frontend-app/.env

# GraphQL Backend
cp backend-graphql/.env.example backend-graphql/.env

# Python Backend (if needed)
# Edit DATABASE_URL, NEO4J credentials if different
```

### Step 5: Start Development Servers

Open **three separate terminals**:

**Terminal 1 - Python Backend:**
```bash
make dev-backend-py
# or
cd backend-python
uvicorn api.app:app --reload --port 8000
```

**Terminal 2 - GraphQL Backend:**
```bash
make dev-backend-gql
# or
cd backend-graphql
npm run dev
```

**Terminal 3 - Frontend:**
```bash
make dev-frontend
# or
cd frontend-app
npm run dev
```

## 🌐 Access Applications

Once all services are running:

- **Frontend UI**: http://localhost:3000
- **GraphQL API**: http://localhost:4000/graphql
- **Python REST API**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (user: neo4j, pass: test)

## 🔧 Detailed Setup Instructions

### Frontend Application Setup

```bash
cd frontend-app

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

**Environment Variables** (`.env`):
```env
REACT_APP_GRAPHQL_URI=http://localhost:4000/graphql
```

### GraphQL Backend Setup

```bash
cd backend-graphql

# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Run development server
npm run dev

# Run in production
npm start
```

**Environment Variables** (`.env`):
```env
NODE_ENV=development
PORT=4000
DATABASE_URL=postgresql://honestly:honestly123@localhost:5432/honestly
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=test
GRAPHQL_PATH=/graphql
CORS_ORIGIN=http://localhost:3000
```

### Python Backend Setup

```bash
cd backend-python

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn api.app:app --reload --port 8000
```

**Environment Variables**:
The Python backend reads from environment or uses defaults. You can set:
```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=test
export KAFKA_BOOTSTRAP=localhost:9092
```

## 🧪 Testing

### Run All Tests

```bash
make test
```

### Test Individual Components

```bash
# Frontend
cd frontend-app
npm test

# GraphQL Backend
cd backend-graphql
npm test

# Python Backend
cd backend-python
pytest
```

## 🐛 Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Check what's using the port
lsof -i :3000  # Frontend
lsof -i :4000  # GraphQL Backend
lsof -i :8000  # Python Backend

# Kill the process or change the port in config
```

### Docker Services Not Starting

```bash
# Check Docker is running
docker ps

# View logs
docker-compose logs

# Restart services
make down
make up
```

### Neo4j Connection Issues

```bash
# Check Neo4j is running
docker ps | grep neo4j

# Access Neo4j browser
open http://localhost:7474

# Check logs
docker logs honestly-neo4j
```

### Database Migrations

If you need to reset the database:

```bash
# GraphQL Backend (if using Prisma)
cd backend-graphql
npm run prisma:migrate reset

# Neo4j
docker exec honestly-neo4j cypher-shell -u neo4j -p test "MATCH (n) DETACH DELETE n"
```

## 📦 Production Deployment

### Using Docker

```bash
# Build all containers
docker-compose -f docker-compose.prod.yml build

# Start in production mode
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

1. **Frontend**: Build and serve static files
   ```bash
   cd frontend-app
   npm run build
   # Serve the dist/ directory with nginx or similar
   ```

2. **GraphQL Backend**: Run with PM2 or similar
   ```bash
   cd backend-graphql
   npm install --production
   pm2 start src/index.js --name honestly-graphql
   ```

3. **Python Backend**: Run with Gunicorn
   ```bash
   cd backend-python
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.app:app
   ```

## 🔐 Security Checklist

Before deploying to production:

- [ ] Change default database passwords
- [ ] Set `NODE_ENV=production`
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS/TLS
- [ ] Set up authentication (JWT tokens)
- [ ] Configure rate limiting
- [ ] Enable logging and monitoring
- [ ] Set up backup strategies
- [ ] Review and update security headers
- [ ] Implement input validation
- [ ] Set up firewall rules

## 📚 Additional Resources

- [Frontend README](frontend-app/README.md) - Detailed frontend documentation
- [GraphQL Backend README](backend-graphql/README.md) - Backend API documentation
- [Python Backend README](backend-python/README.md) - Vault API documentation
- [Vault API Docs](docs/vault-api.md) - Complete API reference
- [Architecture Overview](docs/Scope.md) - System architecture

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/aresforblue-ai/honestly/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aresforblue-ai/honestly/discussions)
- **Documentation**: [docs/](docs/)

## 📝 Next Steps

1. Explore the frontend at http://localhost:3000
2. Try the GraphQL playground at http://localhost:4000/graphql
3. Check the REST API docs at http://localhost:8000/docs
4. Review the documentation in the `docs/` folder
5. Start building your own features!

---

**Happy Building! 🚀**
