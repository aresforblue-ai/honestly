# Copilot Instructions for Honestly

This document provides instructions for GitHub Copilot coding agent to work effectively with the Honestly Truth Engine & Personal Proof Vault repository.

## 📋 Repository Overview

Honestly is a comprehensive blockchain-verified identity and credential verification system with three main components:

1. **Frontend Application** (`frontend-app/`) - React + Vite + TailwindCSS + Apollo Client
2. **GraphQL Backend** (`backend-graphql/`) - Node.js + Apollo Server + Express
3. **Python Backend** (`backend-python/`) - FastAPI + Neo4j + Kafka + Hyperledger Fabric

## 🏗️ Project Structure

```
honestly/
├── frontend-app/           # React frontend (port 3000)
├── backend-graphql/        # Node.js GraphQL API (port 4000)
├── backend-python/         # Python FastAPI backend (port 8000)
├── docs/                   # Documentation
├── neo4j/                  # Database initialization scripts
├── docker/                 # Docker configuration
└── docker-compose.yml      # Infrastructure orchestration
```

## 🛠️ Development Commands

### Installation
```bash
make install                # Install all dependencies
cd frontend-app && npm install
cd backend-graphql && npm install
cd backend-python && pip install -r requirements.txt
```

### Running Services
```bash
make up                     # Start Docker infrastructure
make dev-frontend           # Start React dev server (port 3000)
make dev-backend-gql        # Start GraphQL server (port 4000)
make dev-backend-py         # Start Python API (port 8000)
```

### Testing
```bash
make test                   # Run all tests
cd frontend-app && npm test
cd backend-graphql && npm test
cd backend-python && pytest
```

### Linting
```bash
cd frontend-app && npm run lint
cd backend-graphql && npm run lint
```

### Cleanup
```bash
make clean                  # Remove build artifacts and dependencies
make down                   # Stop Docker services
```

## 📝 Coding Standards & Conventions

### General Guidelines
- Write clear, self-documenting code
- Follow existing code style in each component
- Keep functions small and focused
- Use meaningful variable and function names
- Add comments only when necessary to explain complex logic

### Frontend (React/JavaScript)
- Use functional components with hooks
- Always import React at the top of component files
- Follow React best practices
- Use ES6+ features (arrow functions, destructuring, async/await)
- Component files should use JSX extension
- Style with TailwindCSS utility classes
- Keep components modular and reusable

**Example:**
```javascript
// frontend-app/src/components/AppCard.jsx
import React from 'react';

const AppCard = ({ app }) => {
  const { name, platform, whistlerScore, grade } = app;
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold">{name}</h3>
      <p className="text-gray-600">{platform}</p>
      <div className="mt-4">
        <span className="text-2xl font-bold">{whistlerScore}</span>
        <span className="ml-2 text-lg">Grade: {grade}</span>
      </div>
    </div>
  );
};

export default AppCard;
```

### Backend GraphQL (Node.js)
- Use ES6 modules (type: "module" in package.json)
- Implement proper error handling
- Use async/await for asynchronous operations
- Follow GraphQL schema-first design
- Organize resolvers by type
- Use Winston for structured logging

**Example:**
```javascript
// backend-graphql/src/graphql/resolvers/appResolvers.js
export const appResolvers = {
  Query: {
    app: async (_, { id }, { dataSources }) => {
      try {
        return await dataSources.appAPI.getAppById(id);
      } catch (error) {
        logger.error('Failed to fetch app', { id, error: error.message });
        throw new Error('Could not retrieve app');
      }
    },
  },
};
```

### Backend Python (FastAPI)
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Implement proper error handling with FastAPI exceptions
- Use Pydantic models for request/response validation
- Keep routes organized in separate modules
- Use async/await for I/O operations

**Example:**
```python
# backend-python/api/routes/vault.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class DocumentUpload(BaseModel):
    type: str
    data: str
    metadata: Optional[dict] = None

@router.post("/vault/upload")
async def upload_document(doc: DocumentUpload):
    try:
        # Process document upload
        result = await vault_service.store_document(doc)
        return {"id": result.id, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Database
- **Neo4j**: Use parameterized queries to prevent injection
- **PostgreSQL**: Use Prisma ORM for type-safe database access
- Always use transactions for multi-step operations
- Add proper indexes for frequently queried fields

## 🔐 Security Boundaries & Sensitive Areas

### ⚠️ NEVER MODIFY OR TOUCH:
- `.env` files or environment variables (read-only)
- Docker secrets and credentials
- Private keys or cryptographic material
- Hyperledger Fabric network configuration
- Production database connection strings

### 🔒 SECURITY REQUIREMENTS:
- Always validate and sanitize user input
- Use parameterized queries for all database operations
- Implement proper authentication checks (when adding auth)
- Never log sensitive data (passwords, tokens, keys)
- Use HTTPS/TLS for all external communications
- Implement rate limiting on public endpoints
- Follow OWASP security best practices

### 📌 Encryption & ZK Proofs:
- Personal documents use AES-256-GCM encryption
- ZK proofs enable selective disclosure without revealing underlying data
- Never bypass encryption for convenience
- Always verify proof validity before trusting claims

## 🧪 Testing Guidelines

### Frontend Tests
- Write unit tests for utility functions
- Test component rendering with React Testing Library
- Mock GraphQL queries with MockedProvider
- Test user interactions and state changes

### Backend Tests
- Write unit tests for resolvers and services
- Mock database calls in unit tests
- Write integration tests for API endpoints
- Test error handling and edge cases
- Aim for >80% code coverage

### Python Tests
- Use pytest for all tests
- Mock external dependencies (Neo4j, Kafka, Fabric)
- Test both success and failure paths
- Include async test cases

## 🎯 Task Guidance

### Good Tasks for Copilot:
- Adding new GraphQL queries or mutations
- Creating new React components
- Implementing new API endpoints
- Writing tests for existing code
- Fixing bugs with clear reproduction steps
- Updating documentation
- Improving error handling
- Adding input validation
- Refactoring small, isolated functions

### Tasks Requiring Human Review:
- Changes to authentication/authorization logic
- Modifying encryption or ZK proof implementation
- Altering blockchain integration
- Database schema migrations
- Infrastructure changes (Docker, CI/CD)
- Security-critical code
- Complex refactoring across multiple components

## 📚 Key Dependencies & Technologies

### Frontend
- **React 18.2** - UI library
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Apollo Client** - GraphQL client
- **React Router** - Navigation

### GraphQL Backend
- **Apollo Server 4.9** - GraphQL server
- **Express 4.18** - Web framework
- **Prisma 5.7** - ORM
- **Winston 3.11** - Logging
- **Helmet** - Security headers

### Python Backend
- **FastAPI** - Web framework
- **Neo4j** - Graph database
- **Kafka** - Event streaming
- **FAISS** - Vector search
- **Hyperledger Fabric** - Blockchain
- **Pydantic** - Data validation

## 🚀 Git Workflow

### Branch Naming
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Documentation: `docs/description`
- Copilot branches: `copilot/task-description`

### Commit Messages
- Use conventional commit format
- Be descriptive but concise
- Examples:
  - `feat: add document encryption endpoint`
  - `fix: resolve Neo4j connection timeout`
  - `docs: update API documentation`
  - `test: add tests for vault service`

## 📖 Additional Resources

- [Architecture Documentation](/ARCHITECTURE.md)
- [Setup Guide](/SETUP.md)
- [Vault API Documentation](/docs/vault-api.md)
- [Vault Quick Start](/docs/vault-quickstart.md)
- [Project Scope](/docs/Scope.md)

## ⚡ Performance Considerations

- Frontend: Lazy load components, optimize bundle size
- GraphQL: Use DataLoader to batch database queries
- Python: Use async operations for I/O-bound tasks
- Database: Add indexes for frequently queried fields
- Cache responses where appropriate

## 🐛 Common Issues & Solutions

### Port Already in Use
```bash
# Check what's using the port
lsof -i :3000  # Frontend
lsof -i :4000  # GraphQL
lsof -i :8000  # Python
```

### Docker Services Not Starting
```bash
make down && make up
docker-compose logs
```

### Neo4j Connection Issues
```bash
docker ps | grep neo4j
docker logs honestly-neo4j
```

## 💡 Best Practices

1. **Always run tests** after making code changes
2. **Use the existing code style** in each component
3. **Keep changes minimal** and focused on the task
4. **Document complex logic** with clear comments
5. **Validate input** at API boundaries
6. **Handle errors gracefully** with meaningful messages
7. **Use type safety** (TypeScript types, Python type hints, Pydantic models)
8. **Follow the DRY principle** - avoid code duplication
9. **Write self-documenting code** with clear naming
10. **Test edge cases** and error conditions

## 🎓 Learning Resources

- **GraphQL**: https://graphql.org/learn/
- **Apollo Server**: https://apollographql.com/docs/apollo-server/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Neo4j Cypher**: https://neo4j.com/developer/cypher/
- **React**: https://react.dev/
- **Hyperledger Fabric**: https://hyperledger-fabric.readthedocs.io/

---

**Remember**: This is a development MVP. Production deployment requires additional security hardening, proper authentication, production-grade blockchain network, and comprehensive monitoring.
