import { GraphQLError } from 'graphql';
import logger from '../utils/logger.js';

// Mock data for MVP - replace with actual database calls
const mockApps = [
  {
    id: '1',
    name: 'TrustApp Pro',
    platform: 'ANDROID',
    appStoreId: 'com.trust.app',
    whistlerScore: 85,
    metadata: {},
    reviews: [],
    claims: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '2',
    name: 'SecureChat',
    platform: 'IOS',
    appStoreId: 'com.secure.chat',
    whistlerScore: 92,
    metadata: {},
    reviews: [],
    claims: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

export const resolvers = {
  Query: {
    app: (_, { id }) => {
      logger.info(`Fetching app with id: ${id}`);
      const app = mockApps.find(a => a.id === id);
      if (!app) {
        throw new GraphQLError('App not found', {
          extensions: { code: 'NOT_FOUND' },
        });
      }
      return app;
    },

    apps: (_, { limit = 10, offset = 0 }) => {
      logger.info(`Fetching apps: limit=${limit}, offset=${offset}`);
      return mockApps.slice(offset, offset + limit);
    },

    reviews: (_, { appId, limit = 10 }) => {
      logger.info(`Fetching reviews for app: ${appId}`);
      return [];
    },

    claim: (_, { id }) => {
      logger.info(`Fetching claim with id: ${id}`);
      return null;
    },

    scoreApp: (_, { appId }) => {
      logger.info(`Calculating score for app: ${appId}`);
      const app = mockApps.find(a => a.id === appId);
      if (!app) {
        throw new GraphQLError('App not found', {
          extensions: { code: 'NOT_FOUND' },
        });
      }

      const score = app.whistlerScore || 70;
      const grade = score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F';

      return {
        appId,
        score,
        grade,
        breakdown: {
          privacy: { value: Math.floor(Math.random() * 30) + 60 },
          financial: { value: Math.floor(Math.random() * 30) + 60 },
        },
      };
    },
  },

  Mutation: {
    registerApp: (_, args) => {
      logger.info(`Registering new app: ${args.name}`);
      const newApp = {
        id: String(mockApps.length + 1),
        name: args.name,
        platform: args.platform,
        appStoreId: args.appStoreId || null,
        whistlerScore: 70,
        metadata: args.metadata || {},
        reviews: [],
        claims: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      mockApps.push(newApp);
      return newApp;
    },

    addReview: (_, { appId, source, content, rating }) => {
      logger.info(`Adding review for app: ${appId}`);
      return {
        id: String(Date.now()),
        appId,
        source,
        content,
        rating,
        sentiment: {},
        createdAt: new Date().toISOString(),
      };
    },
  },

  App: {
    reviews: (parent) => parent.reviews || [],
    claims: (parent) => parent.claims || [],
  },
};
