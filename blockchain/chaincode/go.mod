module vault_anchor

go 1.21

require (
	github.com/hyperledger/fabric-contract-api-go v1.2.2
	github.com/hyperledger/fabric-protos-go v0.3.0
)

// Note: Dilithium post-quantum signatures would require additional library
// For MVP, using standard crypto/sha256 and crypto/ecdsa
// In production, integrate: github.com/pq-crystals/dilithium

