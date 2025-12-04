import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { ApolloServerPluginDrainHttpServer } from '@apollo/server/plugin/drainHttpServer';
import http from 'http';
import { typeDefs } from '../graphql/schema.js';
import { resolvers } from '../graphql/resolvers.js';
import { serverConfig } from '../config/server.js';
import logger from '../utils/logger.js';

export async function createApolloServer(app) {
  const httpServer = http.createServer(app);

  const server = new ApolloServer({
    typeDefs,
    resolvers,
    plugins: [
      ApolloServerPluginDrainHttpServer({ httpServer }),
    ],
    formatError: (error) => {
      logger.error('GraphQL Error:', error);
      return error;
    },
  });

  await server.start();
  logger.info('Apollo Server started successfully');

  app.use(
    serverConfig.graphqlPath,
    expressMiddleware(server, {
      context: async ({ req }) => ({
        req,
      }),
    })
  );

  return httpServer;
}
