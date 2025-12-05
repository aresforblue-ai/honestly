export const typeDefs = `#graphql
  scalar JSON
  scalar DateTime

  enum Platform {
    ANDROID
    IOS
    WEB
    OTHER
  }

  enum VerdictOutcome {
    TRUE
    FALSE
    MIXED
    UNDETERMINED
  }

  type App {
    id: ID!
    name: String!
    platform: Platform!
    appStoreId: String
    whistlerScore: Int
    metadata: JSON
    reviews: [Review!]!
    claims: [Claim!]!
    createdAt: DateTime!
    updatedAt: DateTime!
  }

  type Review {
    id: ID!
    appId: ID!
    source: String!
    content: String!
    rating: Int
    sentiment: JSON
    createdAt: DateTime!
  }

  type Claim {
    id: ID!
    appId: ID!
    statement: String!
    scope: String
    claimHash: String!
    evidence: [Evidence!]!
    verdicts: [Verdict!]!
    createdAt: DateTime!
    updatedAt: DateTime!
  }

  type Evidence {
    id: ID!
    claimId: ID!
    text: String
    snapshot: String
    snapshotHash: String
    createdAt: DateTime!
  }

  type Verdict {
    id: ID!
    claimId: ID!
    outcome: VerdictOutcome!
    confidence: Float
    reasoning: String!
    createdAt: DateTime!
  }

  type ScoreBreakdownItem {
    value: Int!
  }

  type ScoreBreakdown {
    privacy: ScoreBreakdownItem!
    financial: ScoreBreakdownItem!
  }

  type ScoreResult {
    appId: ID!
    score: Int!
    grade: String!
    breakdown: ScoreBreakdown!
  }

  type Query {
    app(id: ID!): App
    apps(limit: Int, offset: Int): [App!]!
    reviews(appId: ID!, limit: Int): [Review!]!
    claim(id: ID!): Claim
    scoreApp(appId: ID!): ScoreResult!
  }

  type Mutation {
    registerApp(
      platform: Platform!
      appStoreId: String
      name: String!
      metadata: JSON
    ): App!
    
    addReview(appId: ID!, source: String!, content: String!, rating: Int): Review!
  }
`;
