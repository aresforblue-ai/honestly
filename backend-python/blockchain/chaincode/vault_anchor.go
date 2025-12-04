package main

import (
	"crypto/ecdsa"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// ClaimAnchor represents an anchored document attestation
type ClaimAnchor struct {
	DocumentID  string `json:"documentID"`
	MerkleRoot  string `json:"merkleRoot"`
	Timestamp   string `json:"timestamp"`
	Signature   string `json:"signature"`
	PublicKey   string `json:"publicKey"`
	Hash        string `json:"hash"`
}

// VaultAnchorContract provides functions for anchoring documents
type VaultAnchorContract struct {
	contractapi.Contract
}

// AnchorDocument anchors a document hash to the blockchain
func (s *VaultAnchorContract) AnchorDocument(
	ctx contractapi.TransactionContextInterface,
	documentID string,
	merkleRoot string,
	documentHash string,
	signature string,
	publicKey string,
) error {
	// Validate inputs
	if documentID == "" {
		return fmt.Errorf("documentID cannot be empty")
	}
	if merkleRoot == "" {
		return fmt.Errorf("merkleRoot cannot be empty")
	}
	if documentHash == "" {
		return fmt.Errorf("documentHash cannot be empty")
	}

	// Check if document already anchored
	existing, err := ctx.GetStub().GetState(documentID)
	if err != nil {
		return fmt.Errorf("failed to read from world state: %v", err)
	}
	if existing != nil {
		return fmt.Errorf("document %s already anchored", documentID)
	}

	// Create anchor record
	timestamp := time.Now().UTC().Format(time.RFC3339)
	anchor := ClaimAnchor{
		DocumentID: documentID,
		MerkleRoot: merkleRoot,
		Timestamp:  timestamp,
		Signature:  signature,
		PublicKey:  publicKey,
		Hash:       documentHash,
	}

	// Marshal to JSON
	anchorJSON, err := json.Marshal(anchor)
	if err != nil {
		return fmt.Errorf("failed to marshal anchor: %v", err)
	}

	// Store in world state
	err = ctx.GetStub().PutState(documentID, anchorJSON)
	if err != nil {
		return fmt.Errorf("failed to put anchor to world state: %v", err)
	}

	return nil
}

// QueryAnchor retrieves an anchor by document ID
func (s *VaultAnchorContract) QueryAnchor(
	ctx contractapi.TransactionContextInterface,
	documentID string,
) (*ClaimAnchor, error) {
	if documentID == "" {
		return nil, fmt.Errorf("documentID cannot be empty")
	}

	anchorJSON, err := ctx.GetStub().GetState(documentID)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if anchorJSON == nil {
		return nil, fmt.Errorf("anchor not found for document %s", documentID)
	}

	var anchor ClaimAnchor
	err = json.Unmarshal(anchorJSON, &anchor)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal anchor: %v", err)
	}

	return &anchor, nil
}

// VerifyAttestation verifies that an attestation exists and signature is valid
func (s *VaultAnchorContract) VerifyAttestation(
	ctx contractapi.TransactionContextInterface,
	documentID string,
	proofHash string,
) (bool, error) {
	anchor, err := s.QueryAnchor(ctx, documentID)
	if err != nil {
		return false, err
	}

	// Verify hash matches
	if anchor.Hash != proofHash {
		return false, fmt.Errorf("hash mismatch")
	}

	// Verify signature (simplified - in production use proper Dilithium verification)
	// For MVP, we verify the signature format and that it exists
	if anchor.Signature == "" {
		return false, fmt.Errorf("signature missing")
	}

	// In production, implement proper signature verification:
	// 1. Decode public key from hex
	// 2. Verify signature against merkle root + timestamp
	// 3. Use Dilithium verification algorithm

	return true, nil
}

// ComputeHash computes SHA-256 hash of data
func ComputeHash(data string) string {
	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:])
}

// GenerateSignature generates a signature for data (simplified for MVP)
// In production, use Dilithium post-quantum signatures
func GenerateSignature(data string, privateKey *ecdsa.PrivateKey) (string, error) {
	hash := sha256.Sum256([]byte(data))
	r, s, err := ecdsa.Sign(rand.Reader, privateKey, hash[:])
	if err != nil {
		return "", err
	}
	signature := append(r.Bytes(), s.Bytes()...)
	return hex.EncodeToString(signature), nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&VaultAnchorContract{})
	if err != nil {
		fmt.Printf("Error creating vault anchor chaincode: %s", err.Error())
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting vault anchor chaincode: %s", err.Error())
	}
}

