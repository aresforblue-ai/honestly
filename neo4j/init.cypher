// Constraints & indexes
CREATE CONSTRAINT claim_id_unique IF NOT EXISTS FOR (c:Claim) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT source_name_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.name IS UNIQUE;
CREATE INDEX claim_state IF NOT EXISTS FOR (c:Claim) ON (c.state);