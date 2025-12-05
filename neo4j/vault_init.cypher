// Neo4j schema extensions for Personal Proof Vault MVP

// Constraints for Document nodes
CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE INDEX document_user_id IF NOT EXISTS FOR (d:Document) ON (d.user_id);
CREATE INDEX document_type IF NOT EXISTS FOR (d:Document) ON (d.document_type);
CREATE INDEX document_hash IF NOT EXISTS FOR (d:Document) ON (d.hash);

// Constraints for User nodes
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;

// Constraints for Attestation nodes
CREATE CONSTRAINT attestation_id_unique IF NOT EXISTS FOR (a:Attestation) REQUIRE a.id IS UNIQUE;
CREATE INDEX attestation_document_id IF NOT EXISTS FOR (a:Attestation) ON (a.document_id);
CREATE INDEX attestation_fabric_tx_id IF NOT EXISTS FOR (a:Attestation) ON (a.fabric_tx_id);

// Constraints for TimelineEvent nodes
CREATE INDEX timeline_user_id IF NOT EXISTS FOR (t:TimelineEvent) ON (t.user_id);
CREATE INDEX timeline_event_type IF NOT EXISTS FOR (t:TimelineEvent) ON (t.event_type);
CREATE INDEX timeline_timestamp IF NOT EXISTS FOR (t:TimelineEvent) ON (t.timestamp);

// Constraints for ProofLink nodes
CREATE CONSTRAINT proof_link_token_unique IF NOT EXISTS FOR (p:ProofLink) REQUIRE p.share_token IS UNIQUE;
CREATE INDEX proof_link_document_id IF NOT EXISTS FOR (p:ProofLink) ON (p.document_id);

// Example: Create a test user (optional, for development)
// MERGE (u:User {id: "test_user_1"})
// SET u.created_at = datetime()
// RETURN u;

