/**
 * Neo4j Database Connection
 * 
 * Provides connection pooling and session management for Neo4j queries.
 */

import neo4j from 'neo4j-driver';
import { env } from './env.js';
import logger from '../utils/logger.js';

// Create driver with connection pooling
const driver = neo4j.driver(
  env.NEO4J_URI,
  neo4j.auth.basic(env.NEO4J_USER, env.NEO4J_PASSWORD),
  {
    maxConnectionPoolSize: 50,
    connectionAcquisitionTimeout: 60000,
    maxTransactionRetryTime: 30000,
  }
);

// Verify connectivity on startup
driver.verifyConnectivity()
  .then(() => logger.info('Neo4j connection established'))
  .catch(err => logger.warn(`Neo4j connection failed: ${err.message}`));

/**
 * Get a session for database operations.
 * Remember to close the session after use.
 */
export const getSession = () => driver.session();

/**
 * Execute a read query.
 * 
 * @param {string} query - Cypher query
 * @param {Object} params - Query parameters
 * @returns {Promise<Array>} Query results
 */
export const readQuery = async (query, params = {}) => {
  const session = getSession();
  try {
    const result = await session.run(query, params);
    return result.records.map(record => record.toObject());
  } finally {
    await session.close();
  }
};

/**
 * Execute a write query.
 * 
 * @param {string} query - Cypher query
 * @param {Object} params - Query parameters
 * @returns {Promise<Array>} Query results
 */
export const writeQuery = async (query, params = {}) => {
  const session = getSession();
  try {
    const result = await session.run(query, params);
    return result.records.map(record => record.toObject());
  } finally {
    await session.close();
  }
};

/**
 * Close the driver connection (for graceful shutdown).
 */
export const closeConnection = async () => {
  await driver.close();
  logger.info('Neo4j connection closed');
};

export default { driver, getSession, readQuery, writeQuery, closeConnection };

