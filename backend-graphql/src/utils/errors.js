import { GraphQLError } from 'graphql';

export class ValidationError extends GraphQLError {
  constructor(message) {
    super(message, {
      extensions: {
        code: 'VALIDATION_ERROR',
        http: { status: 400 },
      },
    });
  }
}

export class NotFoundError extends GraphQLError {
  constructor(message) {
    super(message, {
      extensions: {
        code: 'NOT_FOUND',
        http: { status: 404 },
      },
    });
  }
}

export class AuthenticationError extends GraphQLError {
  constructor(message) {
    super(message, {
      extensions: {
        code: 'UNAUTHENTICATED',
        http: { status: 401 },
      },
    });
  }
}

export class ForbiddenError extends GraphQLError {
  constructor(message) {
    super(message, {
      extensions: {
        code: 'FORBIDDEN',
        http: { status: 403 },
      },
    });
  }
}
