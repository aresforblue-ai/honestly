"""
Tests for AAIP ZK Integration
=============================

Tests the full flow of:
1. Agent registration
2. Reputation tracking
3. ZK reputation proofs
4. Nullifier tracking
5. Signature verification
"""

import pytest
import json
from unittest.mock import Mock, patch

# Import AAIP components
from identity.ai_agent_protocol import (
    AIAgentRegistry,
    AgentIdentity,
    AgentCapability,
    AgentConstraint,
    AgentAuthenticator,
    register_ai_agent,
    verify_agent_capability,
    get_agent_reputation,
    reset_registry,
    compute_model_fingerprint,
)

from identity.zkp_integration import (
    AAIPZKIntegration,
    ZKProofResult,
    get_zkp_integration,
    prove_agent_reputation_zk,
    verify_agent_reputation_proof,
)


class TestAgentRegistration:
    """Test agent registration and identity."""
    
    def setup_method(self):
        """Reset registry before each test."""
        reset_registry()
    
    def test_register_agent_basic(self):
        """Test basic agent registration."""
        result = register_ai_agent(
            name="test-agent",
            operator_id="op_123",
            operator_name="Test Operator",
            model_family="transformer",
            capabilities=["text_generation", "reasoning"],
            constraints=["audit_logged"],
            public_key="",
            is_human_backed=True,
        )
        
        assert result["success"] is True
        assert "agent_id" in result
        assert result["did"].startswith("did:honestly:agent:")
        assert "model_fingerprint" in result
    
    def test_register_agent_with_model_fingerprint(self):
        """Test registration with explicit model fingerprint."""
        result = register_ai_agent(
            name="gpt-4-turbo",
            operator_id="op_openai",
            operator_name="OpenAI",
            model_family="transformer",
            capabilities=["text_generation", "code_generation", "reasoning"],
            constraints=["rate_limited"],
            public_key="",
            model_version="0613",
            weights_hash="abc123",  # Would be actual hash in production
        )
        
        assert result["success"] is True
        assert len(result["model_fingerprint"]) == 64  # SHA256 hex
    
    def test_model_fingerprint_deterministic(self):
        """Test that model fingerprint is deterministic."""
        fp1 = compute_model_fingerprint(
            model_name="claude-3",
            model_version="opus",
            model_family="transformer",
        )
        
        fp2 = compute_model_fingerprint(
            model_name="claude-3",
            model_version="opus",
            model_family="transformer",
        )
        
        assert fp1 == fp2
        
        # Different inputs = different fingerprint
        fp3 = compute_model_fingerprint(
            model_name="claude-3",
            model_version="sonnet",  # Changed
            model_family="transformer",
        )
        
        assert fp1 != fp3


class TestAgentCapabilities:
    """Test capability verification."""
    
    def setup_method(self):
        reset_registry()
    
    def test_verify_existing_capability(self):
        """Test verifying a capability the agent has."""
        result = register_ai_agent(
            name="capable-agent",
            operator_id="op_1",
            operator_name="Operator",
            model_family="transformer",
            capabilities=["text_generation", "code_generation"],
            constraints=[],
            public_key="",
        )
        
        agent_id = result["agent_id"]
        
        cap_result = verify_agent_capability(agent_id, "text_generation")
        
        assert cap_result["success"] is True
        assert cap_result["capability"] == "text_generation"
        assert "proof_commitment" in cap_result or "commitment" in str(cap_result)
    
    def test_verify_missing_capability(self):
        """Test verifying a capability the agent doesn't have."""
        result = register_ai_agent(
            name="limited-agent",
            operator_id="op_1",
            operator_name="Operator",
            model_family="transformer",
            capabilities=["text_generation"],  # No code_generation
            constraints=[],
            public_key="",
        )
        
        agent_id = result["agent_id"]
        
        cap_result = verify_agent_capability(agent_id, "code_generation")
        
        assert cap_result["success"] is False


class TestReputationSystem:
    """Test reputation tracking and ZK proofs."""
    
    def setup_method(self):
        reset_registry()
    
    def test_initial_reputation(self):
        """Test that new agents start with default reputation."""
        result = register_ai_agent(
            name="new-agent",
            operator_id="op_1",
            operator_name="Operator",
            model_family="transformer",
            capabilities=[],
            constraints=[],
            public_key="",
        )
        
        agent_id = result["agent_id"]
        rep = get_agent_reputation(agent_id)
        
        assert rep["success"] is True
        assert rep["reputation_score"] == 50  # Default starting score
        assert rep["total_interactions"] == 0
    
    def test_reputation_proof_above_threshold(self):
        """Test ZK proof when reputation exceeds threshold."""
        result = register_ai_agent(
            name="good-agent",
            operator_id="op_1",
            operator_name="Operator",
            model_family="transformer",
            capabilities=[],
            constraints=[],
            public_key="",
        )
        
        agent_id = result["agent_id"]
        
        # Get reputation with threshold proof
        rep = get_agent_reputation(agent_id, threshold=40)
        
        assert rep["success"] is True
        assert rep["meets_threshold"] is True
        assert rep["threshold"] == 40
        assert "nullifier" in rep
    
    def test_reputation_proof_below_threshold(self):
        """Test that proof fails when below threshold."""
        result = register_ai_agent(
            name="new-agent",
            operator_id="op_1",
            operator_name="Operator",
            model_family="transformer",
            capabilities=[],
            constraints=[],
            public_key="",
        )
        
        agent_id = result["agent_id"]
        
        # Try to prove 50 > 60 (should fail)
        rep = get_agent_reputation(agent_id, threshold=60)
        
        assert rep["success"] is True
        assert rep["meets_threshold"] is False


class TestNullifierTracking:
    """Test nullifier tracking for replay prevention."""
    
    def setup_method(self):
        reset_registry()
    
    def test_nullifier_uniqueness(self):
        """Test that nullifiers are unique per proof."""
        result = register_ai_agent(
            name="agent",
            operator_id="op_1",
            operator_name="Operator",
            model_family="transformer",
            capabilities=[],
            constraints=[],
            public_key="",
        )
        
        agent_id = result["agent_id"]
        
        # Get two proofs
        rep1 = get_agent_reputation(agent_id, threshold=40)
        rep2 = get_agent_reputation(agent_id, threshold=40)
        
        # Nullifiers should be different (due to salt)
        if rep1.get("nullifier") and rep2.get("nullifier"):
            assert rep1["nullifier"] != rep2["nullifier"]
    
    def test_registry_nullifier_tracking(self):
        """Test registry tracks used nullifiers."""
        registry = AIAgentRegistry()
        
        # Register agent
        identity = registry.register_agent(
            agent_name="test",
            operator_id="op",
            operator_name="Operator",
            model_family="transformer",
            model_hash="abc",
            capabilities=[],
            constraints=[],
            public_key="",
        )
        
        # Simulate proof with nullifier
        proof_data = {
            "proof": None,
            "nullifier": "test_nullifier_123",
            "commitment": "abc",
        }
        
        # First verification should succeed
        is_valid, error = registry.verify_proof_with_nullifier(proof_data)
        assert is_valid is True
        assert error is None
        
        # Second verification with same nullifier should fail (replay)
        is_valid, error = registry.verify_proof_with_nullifier(proof_data)
        assert is_valid is False
        assert "replay" in error.lower()


class TestZKPIntegration:
    """Test the ZKP integration layer."""
    
    def test_zkp_integration_initialization(self):
        """Test ZKP integration initializes correctly."""
        zkp = AAIPZKIntegration()
        
        assert zkp.runner_path is not None
        assert isinstance(zkp.circuits_available, dict)
    
    def test_agent_id_to_field(self):
        """Test agent ID conversion to field element."""
        zkp = AAIPZKIntegration()
        
        field1 = zkp._agent_id_to_field("agent_abc123")
        field2 = zkp._agent_id_to_field("agent_abc123")
        field3 = zkp._agent_id_to_field("agent_xyz789")
        
        # Same input = same output
        assert field1 == field2
        
        # Different input = different output
        assert field1 != field3
        
        # Output is a valid integer string
        int(field1)  # Should not raise
    
    def test_prove_reputation_invalid_score(self):
        """Test proof fails for invalid reputation scores."""
        zkp = AAIPZKIntegration()
        
        # Score > 100 should fail
        result = zkp.prove_reputation_threshold(
            agent_id="agent_1",
            reputation_score=150,
            threshold=50,
        )
        
        assert result.success is False
        assert "0-100" in result.error
    
    def test_prove_reputation_below_threshold(self):
        """Test proof fails when score <= threshold."""
        zkp = AAIPZKIntegration()
        
        result = zkp.prove_reputation_threshold(
            agent_id="agent_1",
            reputation_score=30,
            threshold=50,
        )
        
        assert result.success is False
        assert "threshold" in result.error.lower()


class TestAuthentication:
    """Test agent authentication."""
    
    def setup_method(self):
        reset_registry()
    
    def test_challenge_creation(self):
        """Test challenge creation for authentication."""
        registry = AIAgentRegistry()
        
        # Register agent
        identity = registry.register_agent(
            agent_name="auth-agent",
            operator_id="op",
            operator_name="Operator",
            model_family="transformer",
            model_hash="abc",
            capabilities=[],
            constraints=[],
            public_key="",
        )
        
        auth = AgentAuthenticator(registry)
        challenge_data = auth.create_challenge(identity.agent_id)
        
        assert "challenge" in challenge_data
        assert "nonce" in challenge_data
        assert "expires_at" in challenge_data
        assert "sign_message" in challenge_data
        
        assert len(challenge_data["challenge"]) == 64  # 32 bytes hex
    
    def test_challenge_expiration(self):
        """Test that challenges expire."""
        import time
        
        registry = AIAgentRegistry()
        identity = registry.register_agent(
            agent_name="auth-agent",
            operator_id="op",
            operator_name="Operator",
            model_family="transformer",
            model_hash="abc",
            capabilities=[],
            constraints=[],
            public_key="",
        )
        
        auth = AgentAuthenticator(registry)
        
        # Create challenge with very short expiry (for testing)
        challenge_data = auth.create_challenge(identity.agent_id)
        
        # Manually expire it
        auth.challenge_cache[identity.agent_id]["expires_at"] = time.time() - 1
        
        # Should fail due to expiration
        is_valid, agent, error = auth.verify_challenge_response(
            agent_id=identity.agent_id,
            challenge=challenge_data["challenge"],
            response="test_response_that_is_long_enough",
            signature="test_signature_that_is_long_enough_to_pass",
        )
        
        assert is_valid is False
        assert "expired" in error.lower()


class TestKeyGeneration:
    """Test cryptographic key generation."""
    
    def test_key_pair_generation(self):
        """Test ECDSA key pair generation."""
        try:
            private_key, public_key = AgentAuthenticator.generate_key_pair()
            
            assert "BEGIN PRIVATE KEY" in private_key
            assert "BEGIN PUBLIC KEY" in public_key
        except RuntimeError as e:
            # Skip if cryptography not available
            if "not installed" in str(e):
                pytest.skip("cryptography library not installed")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

