import { createExpressApp } from './loaders/express.js';
import { createApolloServer } from './loaders/apollo.js';
import { serverConfig } from './config/server.js';
import logger from './utils/logger.js';

async function startServer() {
  try {
    logger.info('Starting Honestly GraphQL Backend...');

    const app = createExpressApp();
    const httpServer = await createApolloServer(app);

    httpServer.listen(serverConfig.port, () => {
      logger.info(`🚀 Server running at http://localhost:${serverConfig.port}${serverConfig.graphqlPath}`);
      logger.info(`📊 Health check: http://localhost:${serverConfig.port}/health`);
    });

    // Graceful shutdown
    const shutdown = async () => {
      logger.info('Graceful shutdown initiated...');
      httpServer.close(() => {
        logger.info('HTTP server closed.');
        process.exit(0);
      });
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);

  } catch (err) {
    logger.error('Server failed to start:', err);
    process.exit(1);
  }
}

startServer();
