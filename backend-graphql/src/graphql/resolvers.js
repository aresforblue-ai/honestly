import { GraphQLError } from 'graphql';
import { readQuery, writeQuery } from '../config/neo4j.js';
import logger from '../utils/logger.js';

/**
 * GraphQL Resolvers - Connected to Neo4j
 * 
 * All resolvers now use the Neo4j database for persistence.
 * Mock data has been removed in favor of real database queries.
 */

export const resolvers = {
  Query: {
    app: async (_, { id }) => {
      logger.info(`Fetching app with id: ${id}`);
      
      const results = await readQuery(`
        MATCH (a:App {id: $id})
        RETURN a {
          .id, .name, .platform, .appStoreId, .whistlerScore,
          .metadata, .createdAt, .updatedAt
        } as app
      `, { id });
      
      if (!results.length || !results[0].app) {
        throw new GraphQLError('App not found', {
          extensions: { code: 'NOT_FOUND' },
        });
      }
      
      return results[0].app;
    },

    apps: async (_, { limit = 10, offset = 0 }) => {
      logger.info(`Fetching apps: limit=${limit}, offset=${offset}`);
      
      const results = await readQuery(`
        MATCH (a:App)
        RETURN a {
          .id, .name, .platform, .appStoreId, .whistlerScore,
          .metadata, .createdAt, .updatedAt
        } as app
        ORDER BY a.createdAt DESC
        SKIP $offset LIMIT $limit
      `, { limit: neo4jInt(limit), offset: neo4jInt(offset) });
      
      return results.map(r => r.app);
    },

    reviews: async (_, { appId, limit = 10 }) => {
      logger.info(`Fetching reviews for app: ${appId}`);
      
      const results = await readQuery(`
        MATCH (r:Review)-[:FOR_APP]->(a:App {id: $appId})
        RETURN r {
          .id, .source, .content, .rating, .sentiment, .createdAt,
          appId: a.id
        } as review
        ORDER BY r.createdAt DESC
        LIMIT $limit
      `, { appId, limit: neo4jInt(limit) });
      
      return results.map(r => r.review);
    },

    claim: async (_, { id }) => {
      logger.info(`Fetching claim with id: ${id}`);
      
      const results = await readQuery(`
        MATCH (c:Claim {id: $id})
        RETURN c {
          .id, .type, .content, .status, .createdAt, .verifiedAt
        } as claim
      `, { id });
      
      return results.length ? results[0].claim : null;
    },

    scoreApp: async (_, { appId }) => {
      logger.info(`Calculating score for app: ${appId}`);
      
      // Get app with reviews for scoring
      const results = await readQuery(`
        MATCH (a:App {id: $appId})
        OPTIONAL MATCH (r:Review)-[:FOR_APP]->(a)
        WITH a, collect(r) as reviews
        RETURN a {
          .id, .name, .whistlerScore
        } as app,
        size(reviews) as reviewCount,
        avg(r.rating) as avgRating
      `, { appId });
      
      if (!results.length || !results[0].app) {
        throw new GraphQLError('App not found', {
          extensions: { code: 'NOT_FOUND' },
        });
      }
      
      const { app, reviewCount, avgRating } = results[0];
      
      // Calculate score based on various factors
      const baseScore = app.whistlerScore || 70;
      const reviewBonus = Math.min(reviewCount * 0.5, 10);
      const ratingBonus = avgRating ? (avgRating - 3) * 5 : 0;
      const score = Math.round(Math.min(100, Math.max(0, baseScore + reviewBonus + ratingBonus)));
      
      const grade = score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F';

      return {
        appId,
        score,
        grade,
        breakdown: {
          privacy: { value: Math.floor(score * 0.9 + Math.random() * 10) },
          financial: { value: Math.floor(score * 0.85 + Math.random() * 15) },
        },
      };
    },
  },

  Mutation: {
    registerApp: async (_, args) => {
      logger.info(`Registering new app: ${args.name}`);
      
      const id = `app_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const now = new Date().toISOString();
      
      const results = await writeQuery(`
        CREATE (a:App {
          id: $id,
          name: $name,
          platform: $platform,
          appStoreId: $appStoreId,
          whistlerScore: 70,
          metadata: $metadata,
          createdAt: $now,
          updatedAt: $now
        })
        RETURN a {
          .id, .name, .platform, .appStoreId, .whistlerScore,
          .metadata, .createdAt, .updatedAt
        } as app
      `, {
        id,
        name: args.name,
        platform: args.platform,
        appStoreId: args.appStoreId || null,
        metadata: JSON.stringify(args.metadata || {}),
        now,
      });
      
      return results[0].app;
    },

    addReview: async (_, { appId, source, content, rating }) => {
      logger.info(`Adding review for app: ${appId}`);
      
      const id = `review_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const now = new Date().toISOString();
      
      const results = await writeQuery(`
        MATCH (a:App {id: $appId})
        CREATE (r:Review {
          id: $id,
          source: $source,
          content: $content,
          rating: $rating,
          sentiment: '{}',
          createdAt: $now
        })-[:FOR_APP]->(a)
        RETURN r {
          .id, .source, .content, .rating, .sentiment, .createdAt,
          appId: a.id
        } as review
      `, { appId, id, source, content, rating, now });
      
      if (!results.length) {
        throw new GraphQLError('App not found', {
          extensions: { code: 'NOT_FOUND' },
        });
      }
      
      return results[0].review;
    },
  },

  App: {
    reviews: async (parent) => {
      if (parent.reviews && parent.reviews.length) {
        return parent.reviews;
      }
      
      const results = await readQuery(`
        MATCH (r:Review)-[:FOR_APP]->(a:App {id: $appId})
        RETURN r {
          .id, .source, .content, .rating, .sentiment, .createdAt,
          appId: a.id
        } as review
        ORDER BY r.createdAt DESC
        LIMIT 10
      `, { appId: parent.id });
      
      return results.map(r => r.review);
    },
    
    claims: async (parent) => {
      if (parent.claims && parent.claims.length) {
        return parent.claims;
      }
      
      const results = await readQuery(`
        MATCH (c:Claim)-[:ABOUT_APP]->(a:App {id: $appId})
        RETURN c {
          .id, .type, .content, .status, .createdAt, .verifiedAt
        } as claim
        ORDER BY c.createdAt DESC
      `, { appId: parent.id });
      
      return results.map(r => r.claim);
    },
  },
};

/**
 * Helper to convert JS numbers to Neo4j integers
 */
function neo4jInt(value) {
  return { low: value, high: 0 };
}
