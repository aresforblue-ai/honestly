import express from 'express';
import cors from 'cors';
import { helmetConfig, rateLimitConfig } from '../config/security.js';
import { serverConfig } from '../config/server.js';
import logger from '../utils/logger.js';

export function createExpressApp() {
  const app = express();

  // Security middleware
  app.use(helmetConfig);
  app.use(rateLimitConfig);

  // CORS
  app.use(cors(serverConfig.cors));

  // Body parsing
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Health check endpoint
  app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
  });

  // Request logging
  app.use((req, res, next) => {
    logger.info(`${req.method} ${req.path}`);
    next();
  });

  return app;
}
