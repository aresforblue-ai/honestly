import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { serverConfig } from './server.js';

export const helmetConfig = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ['\'self\''],
      styleSrc: ['\'self\'', '\'unsafe-inline\''],
      scriptSrc: ['\'self\'', '\'unsafe-inline\''],
      imgSrc: ['\'self\'', 'data:', 'https:'],
    },
  },
  crossOriginEmbedderPolicy: false,
});

export const rateLimitConfig = rateLimit({
  windowMs: serverConfig.rateLimit.windowMs,
  max: serverConfig.rateLimit.max,
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});
