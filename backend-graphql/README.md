# Honestly GraphQL Backend

Production-grade Node.js GraphQL API for the AppWhistler Truth Engine, providing app verification, trust scoring, claims management, and evidence tracking.

## 🎯 Features

- **GraphQL API**: Type-safe, flexible query language
- **App Verification**: Register and verify applications
- **Trust Scoring**: Multi-signal WhistlerScore calculation
- **Claims Engine**: Track claims, evidence, and verdicts
- **Provenance Graph**: Link evidence and track trust chains
- **Security**: Helmet, rate limiting, CORS protection
- **Logging**: Winston for structured logging
- **Scalable**: Modular architecture, easy to extend

## 🛠️ Tech Stack

- **Node.js 18+**: JavaScript runtime
- **Apollo Server 4**: GraphQL server
- **Express**: Web framework
- **Prisma**: Database ORM (optional)
- **Winston**: Logging
- **Helmet**: Security headers
- **Express Rate Limit**: DDoS protection

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your configuration

# Run development server
npm run dev

# Run in production
npm start
```

## 📁 Project Structure

```
backend-graphql/
├── src/
│   ├── config/              # Configuration files
│   │   ├── env.js          # Environment variables
│   │   ├── server.js       # Server configuration
│   │   ├── prisma.js       # Database client
│   │   └── security.js     # Security middleware
│   │
│   ├── graphql/            # GraphQL layer
│   │   ├── schema.js       # Type definitions
│   │   └── resolvers.js    # Query/Mutation resolvers
│   │
│   ├── services/           # Business logic
│   │   ├── app.service.js
│   │   ├── review.service.js
│   │   ├── claim.service.js
│   │   ├── scoring/
│   │   └── signals/
│   │
│   ├── loaders/            # Application loaders
│   │   ├── express.js      # Express setup
│   │   └── apollo.js       # Apollo Server setup
│   │
│   ├── utils/              # Utilities
│   │   ├── logger.js
│   │   ├── errors.js
│   │   ├── validation.js
│   │   └── hashing.js
│   │
│   └── index.js            # Application entry point
│
├── prisma/                 # Database schema (optional)
│   └── schema.prisma
│
├── .env.example            # Environment template
├── package.json            # Dependencies
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

```env
NODE_ENV=development
PORT=4000

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/honestly

# Neo4j (if integrating with Python backend)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=test

# API
GRAPHQL_PATH=/graphql

# Security
CORS_ORIGIN=http://localhost:3000
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

## 📝 Available Scripts

```bash
# Development
npm run dev              # Start with nodemon (auto-reload)

# Production
npm start                # Start server
npm run build            # Build for production (if needed)

# Database (Prisma)
npm run prisma:generate  # Generate Prisma client
npm run prisma:migrate   # Run migrations
npm run prisma:studio    # Open Prisma Studio

# Code Quality
npm run lint             # Run ESLint
npm test                 # Run tests
```

## 🔌 GraphQL API

### Schema Overview

```graphql
type App {
  id: ID!
  name: String!
  platform: Platform!
  whistlerScore: Int
  reviews: [Review!]!
  claims: [Claim!]!
}

type Query {
  app(id: ID!): App
  apps(limit: Int, offset: Int): [App!]!
  scoreApp(appId: ID!): ScoreResult!
}

type Mutation {
  registerApp(platform: Platform!, name: String!): App!
  addReview(appId: ID!, content: String!): Review!
}
```

### Example Queries

**Get Apps:**
```graphql
query {
  apps(limit: 10) {
    id
    name
    whistlerScore
  }
}
```

**Get App Details:**
```graphql
query GetAppDetails($id: ID!) {
  app(id: $id) {
    id
    name
    whistlerScore
    claims {
      statement
      verdicts {
        outcome
        confidence
      }
    }
  }
}
```

**Get App Score:**
```graphql
query {
  scoreApp(appId: "1") {
    score
    grade
    breakdown {
      privacy { value }
      financial { value }
    }
  }
}
```

### Example Mutations

**Register App:**
```graphql
mutation {
  registerApp(
    platform: ANDROID
    name: "TrustApp"
    appStoreId: "com.trust.app"
  ) {
    id
    name
    whistlerScore
  }
}
```

## 🏗️ Architecture

### Modular Structure

The backend follows a clean architecture:

1. **Entry Point** (`index.js`): Bootstraps the application
2. **Loaders**: Initialize Express and Apollo Server
3. **GraphQL Layer**: Schema and resolvers
4. **Services**: Business logic (isolated from GraphQL)
5. **Utils**: Shared utilities

### Data Flow

```
Client Request
    ↓
Apollo Server
    ↓
Resolvers
    ↓
Services (Business Logic)
    ↓
Database / External APIs
    ↓
Response
```

## 🔐 Security

### Implemented

- **Helmet**: Security headers
- **CORS**: Configurable origins
- **Rate Limiting**: Per-IP request limits
- **Input Validation**: Custom validators
- **Error Handling**: Sanitized error messages

### Best Practices

```javascript
// Custom error classes
throw new ValidationError('Invalid input');
throw new NotFoundError('App not found');

// Input validation
validateString('name', value, { 
  required: true, 
  minLength: 3, 
  maxLength: 100 
});
```

## 📊 Logging

Winston logger with multiple transports:

```javascript
import logger from './utils/logger.js';

logger.info('Server started');
logger.error('Database connection failed', { error });
logger.debug('Query executed', { query, duration });
```

## 🧪 Testing

```bash
# Run tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

Example test:
```javascript
describe('App Resolver', () => {
  it('should fetch app by ID', async () => {
    const result = await apolloClient.query({
      query: GET_APP,
      variables: { id: '1' }
    });
    expect(result.data.app).toBeDefined();
  });
});
```

## 🚀 Deployment

### Production Build

```bash
# Install production dependencies
npm ci --only=production

# Start with PM2
pm2 start src/index.js --name honestly-backend
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 4000
CMD ["node", "src/index.js"]
```

### Environment Variables

Ensure these are set in production:
- `NODE_ENV=production`
- Database credentials
- CORS origins
- Rate limit settings

## 🔧 Database Integration

### Prisma (Optional)

```bash
# Generate client
npx prisma generate

# Create migration
npx prisma migrate dev --name init

# Apply to production
npx prisma migrate deploy
```

### Neo4j Integration

Connect to existing Neo4j instance:

```javascript
import { env } from './config/env.js';
import neo4j from 'neo4j-driver';

const driver = neo4j.driver(
  env.NEO4J_URI,
  neo4j.auth.basic(env.NEO4J_USER, env.NEO4J_PASSWORD)
);
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process
lsof -i :4000

# Kill process
kill -9 <PID>
```

### Database Connection

```bash
# Test connection
node -e "require('./src/config/prisma.js').prisma.$connect()"
```

### GraphQL Playground Not Loading

Check:
1. Server is running
2. Correct port in browser
3. CORS is configured

## 📚 API Documentation

When server is running, access:
- GraphQL Playground: http://localhost:4000/graphql
- Health Check: http://localhost:4000/health

## 🤝 Contributing

1. Follow Node.js best practices
2. Use ES6+ features
3. Add JSDoc comments
4. Write tests for new features
5. Update documentation

## 📄 License

See [LICENSE](../LICENSE) in repository root.
