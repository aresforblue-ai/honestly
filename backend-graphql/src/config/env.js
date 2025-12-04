import dotenv from 'dotenv';

dotenv.config();

function requireEnv(key, defaultValue) {
  const value = process.env[key] || defaultValue;
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
}

export const env = {
  NODE_ENV: process.env.NODE_ENV || 'development',
  PORT: parseInt(process.env.PORT || '4000', 10),
  
  // Database
  DATABASE_URL: requireEnv('DATABASE_URL', 'postgresql://user:password@localhost:5432/honestly'),
  
  // Neo4j
  NEO4J_URI: process.env.NEO4J_URI || 'bolt://localhost:7687',
  NEO4J_USER: process.env.NEO4J_USER || 'neo4j',
  NEO4J_PASSWORD: process.env.NEO4J_PASSWORD || 'test',
  
  // API
  GRAPHQL_PATH: process.env.GRAPHQL_PATH || '/graphql',
  
  // Security
  CORS_ORIGIN: process.env.CORS_ORIGIN || 'http://localhost:3000',
  RATE_LIMIT_WINDOW_MS: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000', 10),
  RATE_LIMIT_MAX_REQUESTS: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100', 10),
  
  isDevelopment: () => env.NODE_ENV === 'development',
  isProduction: () => env.NODE_ENV === 'production',
};
