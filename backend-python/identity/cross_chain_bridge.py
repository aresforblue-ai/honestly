"""
Cross-Chain Identity Bridge
============================

A revolutionary system for portable identity across multiple blockchains.

This enables:
1. Single identity that works on Ethereum, Polygon, Solana, etc.
2. Cross-chain credential verification
3. Chain-agnostic reputation
4. Unified DID resolution across networks
5. Seamless migration between chains

Architecture:
- Identity anchored on primary chain (Ethereum L1 for security)
- Light proofs replicated to L2s and other chains
- Merkle proofs for cross-chain verification
- Relayer network for trustless bridging
"""

import json
import hashlib
import secrets
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger("identity.bridge")


class Chain(Enum):
    """Supported blockchain networks."""

    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    SOLANA = "solana"
    AVALANCHE = "avalanche"
    BSC = "bsc"
    COSMOS = "cosmos"
    NEAR = "near"


class ChainType(Enum):
    """Types of blockchain networks."""

    EVM = "evm"  # Ethereum Virtual Machine compatible
    SVM = "svm"  # Solana Virtual Machine
    COSMOS_SDK = "cosmos_sdk"
    NEAR_RUNTIME = "near"


# Chain configurations
CHAIN_CONFIG = {
    Chain.ETHEREUM: {
        "type": ChainType.EVM,
        "chain_id": 1,
        "name": "Ethereum Mainnet",
        "rpc": "https://eth.llamarpc.com",
        "explorer": "https://etherscan.io",
        "is_primary": True,  # Primary chain for identity anchoring
    },
    Chain.POLYGON: {
        "type": ChainType.EVM,
        "chain_id": 137,
        "name": "Polygon",
        "rpc": "https://polygon.llamarpc.com",
        "explorer": "https://polygonscan.com",
    },
    Chain.ARBITRUM: {
        "type": ChainType.EVM,
        "chain_id": 42161,
        "name": "Arbitrum One",
        "rpc": "https://arb1.arbitrum.io/rpc",
        "explorer": "https://arbiscan.io",
    },
    Chain.OPTIMISM: {
        "type": ChainType.EVM,
        "chain_id": 10,
        "name": "Optimism",
        "rpc": "https://mainnet.optimism.io",
        "explorer": "https://optimistic.etherscan.io",
    },
    Chain.BASE: {
        "type": ChainType.EVM,
        "chain_id": 8453,
        "name": "Base",
        "rpc": "https://mainnet.base.org",
        "explorer": "https://basescan.org",
    },
    Chain.SOLANA: {
        "type": ChainType.SVM,
        "chain_id": "solana-mainnet",
        "name": "Solana",
        "rpc": "https://api.mainnet-beta.solana.com",
        "explorer": "https://solscan.io",
    },
    Chain.AVALANCHE: {
        "type": ChainType.EVM,
        "chain_id": 43114,
        "name": "Avalanche C-Chain",
        "rpc": "https://api.avax.network/ext/bc/C/rpc",
        "explorer": "https://snowtrace.io",
    },
}


@dataclass
class ChainIdentity:
    """Identity representation on a specific chain."""

    chain: Chain
    address: str  # Chain-specific address/account
    did: str  # DID on this chain
    identity_hash: str  # Hash of identity commitment
    registered_at: str
    last_synced: str
    is_primary: bool = False
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        result = asdict(self)
        result["chain"] = self.chain.value
        return result


@dataclass
class CrossChainIdentity:
    """
    A unified cross-chain identity.

    This represents a single identity that exists across multiple chains.
    """

    universal_did: str  # did:honestly:universal:<id>
    primary_chain: Chain
    primary_address: str
    identity_commitment: str  # Poseidon hash of identity secret

    chain_identities: Dict[str, ChainIdentity] = field(default_factory=dict)
    credentials: List[str] = field(default_factory=list)  # Credential IDs

    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        return {
            "universalDid": self.universal_did,
            "primaryChain": self.primary_chain.value,
            "primaryAddress": self.primary_address,
            "identityCommitment": self.identity_commitment,
            "chainIdentities": {k: v.to_dict() for k, v in self.chain_identities.items()},
            "credentials": self.credentials,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


@dataclass
class BridgeMessage:
    """A message to be bridged across chains."""

    message_id: str
    source_chain: Chain
    target_chain: Chain
    message_type: str
    payload: Dict
    proof: Optional[str] = None
    timestamp: str = ""
    status: str = "pending"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class MerkleProof:
    """Merkle proof for cross-chain verification."""

    root: str
    leaf: str
    path: List[str]
    path_indices: List[int]

    def to_dict(self) -> Dict:
        return asdict(self)

    def verify(self) -> bool:
        """Verify the Merkle proof."""
        current = self.leaf
        for i, sibling in enumerate(self.path):
            if self.path_indices[i] == 0:
                # Current is left, sibling is right
                current = hashlib.sha256(
                    bytes.fromhex(current) + bytes.fromhex(sibling)
                ).hexdigest()
            else:
                # Current is right, sibling is left
                current = hashlib.sha256(
                    bytes.fromhex(sibling) + bytes.fromhex(current)
                ).hexdigest()
        return current == self.root


class ChainAdapter(ABC):
    """Abstract adapter for chain-specific operations."""

    @abstractmethod
    def get_chain(self) -> Chain:
        pass

    @abstractmethod
    def register_identity(self, identity_commitment: str, metadata: Dict) -> str:
        """Register identity on chain, return tx hash."""
        pass

    @abstractmethod
    def verify_identity(self, identity_commitment: str) -> bool:
        """Verify identity exists on chain."""
        pass

    @abstractmethod
    def get_identity_root(self) -> str:
        """Get current identity Merkle root."""
        pass

    @abstractmethod
    def submit_bridge_message(self, message: BridgeMessage) -> str:
        """Submit a bridge message, return tx hash."""
        pass


class EVMChainAdapter(ChainAdapter):
    """Adapter for EVM-compatible chains."""

    def __init__(self, chain: Chain):
        self.chain = chain
        self.config = CHAIN_CONFIG[chain]
        self._identity_registry: Dict[str, Dict] = {}
        self._merkle_root = "0" * 64

    def get_chain(self) -> Chain:
        return self.chain

    def register_identity(self, identity_commitment: str, metadata: Dict) -> str:
        """Register identity (simulated for now)."""
        tx_hash = f"0x{secrets.token_hex(32)}"

        self._identity_registry[identity_commitment] = {
            "commitment": identity_commitment,
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "tx_hash": tx_hash,
        }

        # Update Merkle root (simplified)
        self._update_merkle_root()

        logger.info(f"Registered identity on {self.chain.value}: {identity_commitment[:16]}...")
        return tx_hash

    def verify_identity(self, identity_commitment: str) -> bool:
        return identity_commitment in self._identity_registry

    def get_identity_root(self) -> str:
        return self._merkle_root

    def submit_bridge_message(self, message: BridgeMessage) -> str:
        tx_hash = f"0x{secrets.token_hex(32)}"
        logger.info(f"Bridge message submitted on {self.chain.value}: {message.message_id}")
        return tx_hash

    def _update_merkle_root(self):
        """Update Merkle root after changes."""
        if not self._identity_registry:
            return

        leaves = sorted(self._identity_registry.keys())
        self._merkle_root = self._compute_merkle_root(leaves)

    def _compute_merkle_root(self, leaves: List[str]) -> str:
        """Compute Merkle root from leaves."""
        if not leaves:
            return "0" * 64
        if len(leaves) == 1:
            return leaves[0]

        # Pad to power of 2
        while len(leaves) & (len(leaves) - 1):
            leaves.append(leaves[-1])

        while len(leaves) > 1:
            new_level = []
            for i in range(0, len(leaves), 2):
                combined = hashlib.sha256(
                    bytes.fromhex(leaves[i]) + bytes.fromhex(leaves[i + 1])
                ).hexdigest()
                new_level.append(combined)
            leaves = new_level

        return leaves[0]


class SolanaChainAdapter(ChainAdapter):
    """Adapter for Solana."""

    def __init__(self):
        self.chain = Chain.SOLANA
        self._identity_registry: Dict[str, Dict] = {}
        self._merkle_root = "0" * 64

    def get_chain(self) -> Chain:
        return self.chain

    def register_identity(self, identity_commitment: str, metadata: Dict) -> str:
        """Register identity on Solana (simulated)."""
        # Solana uses base58 addresses
        tx_sig = secrets.token_hex(64)  # Would be actual signature

        self._identity_registry[identity_commitment] = {
            "commitment": identity_commitment,
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "signature": tx_sig,
        }

        logger.info(f"Registered identity on Solana: {identity_commitment[:16]}...")
        return tx_sig

    def verify_identity(self, identity_commitment: str) -> bool:
        return identity_commitment in self._identity_registry

    def get_identity_root(self) -> str:
        return self._merkle_root

    def submit_bridge_message(self, message: BridgeMessage) -> str:
        tx_sig = secrets.token_hex(64)
        logger.info(f"Bridge message submitted on Solana: {message.message_id}")
        return tx_sig


class CrossChainBridge:
    """
    The main cross-chain identity bridge.

    Manages identity synchronization across multiple chains.
    """

    def __init__(self):
        self.adapters: Dict[Chain, ChainAdapter] = {}
        self.identities: Dict[str, CrossChainIdentity] = {}
        self.pending_messages: Dict[str, BridgeMessage] = {}
        self.processed_messages: Dict[str, BridgeMessage] = {}

        # Initialize adapters for supported chains
        self._init_adapters()

    def _init_adapters(self):
        """Initialize chain adapters."""
        for chain, config in CHAIN_CONFIG.items():
            if config["type"] == ChainType.EVM:
                self.adapters[chain] = EVMChainAdapter(chain)
            elif config["type"] == ChainType.SVM:
                self.adapters[chain] = SolanaChainAdapter()

    def create_universal_identity(
        self,
        identity_secret: str,
        primary_chain: Chain,
        primary_address: str,
        metadata: Optional[Dict] = None,
    ) -> CrossChainIdentity:
        """
        Create a new universal cross-chain identity.

        Args:
            identity_secret: The secret seed for the identity
            primary_chain: The primary chain for this identity
            primary_address: The primary address on that chain
            metadata: Additional identity metadata

        Returns:
            CrossChainIdentity instance
        """
        # Generate identity commitment
        identity_commitment = hashlib.sha256(identity_secret.encode()).hexdigest()

        # Generate universal DID
        universal_id = secrets.token_hex(16)
        universal_did = f"did:honestly:universal:{universal_id}"

        # Create identity
        identity = CrossChainIdentity(
            universal_did=universal_did,
            primary_chain=primary_chain,
            primary_address=primary_address,
            identity_commitment=identity_commitment,
        )

        # Register on primary chain
        adapter = self.adapters.get(primary_chain)
        if adapter:
            tx_hash = adapter.register_identity(identity_commitment, metadata or {})

            chain_identity = ChainIdentity(
                chain=primary_chain,
                address=primary_address,
                did=f"did:honestly:{primary_chain.value}:{primary_address}",
                identity_hash=identity_commitment,
                registered_at=datetime.utcnow().isoformat(),
                last_synced=datetime.utcnow().isoformat(),
                is_primary=True,
                metadata={"tx_hash": tx_hash},
            )
            identity.chain_identities[primary_chain.value] = chain_identity

        self.identities[universal_did] = identity

        logger.info(f"Created universal identity: {universal_did}")
        return identity

    def bridge_identity(
        self,
        universal_did: str,
        target_chain: Chain,
        target_address: str,
    ) -> Tuple[ChainIdentity, MerkleProof]:
        """
        Bridge an identity to a new chain.

        Args:
            universal_did: The universal DID to bridge
            target_chain: The target chain
            target_address: Address on target chain

        Returns:
            Tuple of (ChainIdentity, MerkleProof for verification)
        """
        identity = self.identities.get(universal_did)
        if not identity:
            raise ValueError(f"Identity {universal_did} not found")

        if target_chain.value in identity.chain_identities:
            raise ValueError(f"Identity already exists on {target_chain.value}")

        # Get proof from primary chain
        primary_adapter = self.adapters.get(identity.primary_chain)
        if not primary_adapter:
            raise ValueError(f"No adapter for primary chain {identity.primary_chain.value}")

        # Generate Merkle proof
        root = primary_adapter.get_identity_root()
        proof = self._generate_merkle_proof(identity.identity_commitment, root)

        # Create bridge message (for future message queue integration)
        _ = BridgeMessage(
            message_id=f"bridge_{secrets.token_hex(8)}",
            source_chain=identity.primary_chain,
            target_chain=target_chain,
            message_type="IDENTITY_BRIDGE",
            payload={
                "universal_did": universal_did,
                "identity_commitment": identity.identity_commitment,
                "target_address": target_address,
            },
            proof=json.dumps(proof.to_dict()),
        )

        # Submit to target chain
        target_adapter = self.adapters.get(target_chain)
        if target_adapter:
            tx_hash = target_adapter.register_identity(
                identity.identity_commitment,
                {"bridged_from": identity.primary_chain.value, "universal_did": universal_did},
            )

            chain_identity = ChainIdentity(
                chain=target_chain,
                address=target_address,
                did=f"did:honestly:{target_chain.value}:{target_address}",
                identity_hash=identity.identity_commitment,
                registered_at=datetime.utcnow().isoformat(),
                last_synced=datetime.utcnow().isoformat(),
                is_primary=False,
                metadata={"bridged_from": identity.primary_chain.value, "tx_hash": tx_hash},
            )

            identity.chain_identities[target_chain.value] = chain_identity
            identity.updated_at = datetime.utcnow().isoformat()

            logger.info(f"Bridged identity {universal_did} to {target_chain.value}")
            return chain_identity, proof

        raise ValueError(f"No adapter for target chain {target_chain.value}")

    def _generate_merkle_proof(
        self,
        leaf: str,
        root: str,
    ) -> MerkleProof:
        """Generate a Merkle proof (simplified for demo)."""
        # In production, this would query the actual on-chain Merkle tree
        return MerkleProof(
            root=root,
            leaf=leaf,
            path=[secrets.token_hex(32) for _ in range(10)],  # Placeholder
            path_indices=[0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        )

    def verify_cross_chain_identity(
        self,
        universal_did: str,
        chain: Chain,
    ) -> Dict:
        """
        Verify an identity on a specific chain.

        Returns verification result with proof.
        """
        identity = self.identities.get(universal_did)
        if not identity:
            return {"valid": False, "error": "Identity not found"}

        chain_identity = identity.chain_identities.get(chain.value)
        if not chain_identity:
            return {"valid": False, "error": f"Identity not registered on {chain.value}"}

        adapter = self.adapters.get(chain)
        if not adapter:
            return {"valid": False, "error": f"No adapter for {chain.value}"}

        # Verify on chain
        is_valid = adapter.verify_identity(identity.identity_commitment)

        return {
            "valid": is_valid,
            "universal_did": universal_did,
            "chain": chain.value,
            "address": chain_identity.address,
            "identity_commitment": identity.identity_commitment,
            "verified_at": datetime.utcnow().isoformat(),
        }

    def sync_identity(self, universal_did: str) -> Dict:
        """
        Synchronize identity state across all chains.

        Returns sync status for each chain.
        """
        identity = self.identities.get(universal_did)
        if not identity:
            return {"error": "Identity not found"}

        sync_results = {}

        for chain_name, chain_identity in identity.chain_identities.items():
            chain = Chain(chain_name)
            adapter = self.adapters.get(chain)

            if adapter:
                is_valid = adapter.verify_identity(identity.identity_commitment)
                chain_identity.last_synced = datetime.utcnow().isoformat()

                sync_results[chain_name] = {
                    "valid": is_valid,
                    "synced_at": chain_identity.last_synced,
                    "address": chain_identity.address,
                }
            else:
                sync_results[chain_name] = {"error": "No adapter available"}

        identity.updated_at = datetime.utcnow().isoformat()

        return {
            "universal_did": universal_did,
            "chains": sync_results,
            "synced_at": datetime.utcnow().isoformat(),
        }

    def get_identity(self, universal_did: str) -> Optional[Dict]:
        """Get identity details."""
        identity = self.identities.get(universal_did)
        if identity:
            return identity.to_dict()
        return None

    def list_supported_chains(self) -> List[Dict]:
        """List all supported chains."""
        return [
            {
                "chain": chain.value,
                "name": config["name"],
                "type": config["type"].value,
                "chain_id": config["chain_id"],
                "is_primary": config.get("is_primary", False),
            }
            for chain, config in CHAIN_CONFIG.items()
        ]


# ============================================
# DID RESOLVER
# ============================================


class UniversalDIDResolver:
    """
    Resolves DIDs across all supported chains.

    Supports:
    - did:honestly:universal:<id> - Universal cross-chain identity
    - did:honestly:ethereum:<address> - Ethereum-specific identity
    - did:honestly:polygon:<address> - Polygon-specific identity
    - etc.
    """

    def __init__(self, bridge: CrossChainBridge):
        self.bridge = bridge

    def resolve(self, did: str) -> Optional[Dict]:
        """
        Resolve a DID to its document.

        Args:
            did: The DID to resolve

        Returns:
            DID Document or None
        """
        if not did.startswith("did:honestly:"):
            return None

        parts = did.split(":")
        if len(parts) < 4:
            return None

        method = parts[2]
        identifier = parts[3]

        if method == "universal":
            # Resolve universal identity
            identity = self.bridge.get_identity(did)
            if identity:
                return self._create_did_document(did, identity)

        elif method in [c.value for c in Chain]:
            # Resolve chain-specific identity
            _ = Chain(method)  # Validate chain exists
            # Search for identity with this chain identity
            for universal_did, identity_data in self.bridge.identities.items():
                chain_id = identity_data.chain_identities.get(method)
                if chain_id and chain_id.address == identifier:
                    return self._create_did_document(did, identity_data.to_dict())

        return None

    def _create_did_document(self, did: str, identity: Dict) -> Dict:
        """Create a W3C DID Document."""
        return {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://honestly.dev/did/v1",
            ],
            "id": did,
            "controller": did,
            "verificationMethod": [
                {
                    "id": f"{did}#key-1",
                    "type": "EcdsaSecp256k1VerificationKey2019",
                    "controller": did,
                    "publicKeyHex": identity.get("identityCommitment", ""),
                }
            ],
            "authentication": [f"{did}#key-1"],
            "assertionMethod": [f"{did}#key-1"],
            "service": [
                {
                    "id": f"{did}#honestly-service",
                    "type": "HonestlyIdentityService",
                    "serviceEndpoint": "https://api.honestly.dev/identity",
                }
            ],
            "honestlyExtensions": {
                "universalDid": identity.get("universalDid"),
                "primaryChain": identity.get("primaryChain"),
                "chainIdentities": list(identity.get("chainIdentities", {}).keys()),
                "credentialCount": len(identity.get("credentials", [])),
            },
        }


# Global bridge instance
_bridge: Optional[CrossChainBridge] = None


def get_bridge() -> CrossChainBridge:
    """Get the global cross-chain bridge."""
    global _bridge
    if _bridge is None:
        _bridge = CrossChainBridge()
    return _bridge


def get_resolver() -> UniversalDIDResolver:
    """Get the universal DID resolver."""
    return UniversalDIDResolver(get_bridge())
