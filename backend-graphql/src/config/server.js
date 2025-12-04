import { env } from './env.js';

export const serverConfig = {
  port: env.PORT,
  graphqlPath: env.GRAPHQL_PATH,
  cors: {
    origin: env.CORS_ORIGIN,
    credentials: true,
  },
  rateLimit: {
    windowMs: env.RATE_LIMIT_WINDOW_MS,
    max: env.RATE_LIMIT_MAX_REQUESTS,
  },
};
