"""
Encrypted storage service for vault documents using AES-256-GCM.
"""
import os
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

from vault.models import ProofDocument, DocumentType


class VaultStorage:
    """Encrypted storage service for vault documents."""
    
    def __init__(self, encryption_key: Optional[str] = None, storage_path: str = "vault_storage"):
        """
        Initialize vault storage.
        
        Args:
            encryption_key: Base64-encoded encryption key. If None, generates from env or creates new.
            storage_path: Directory path for storing encrypted files.
        """
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        # Get or generate encryption key
        if encryption_key:
            self.master_key = base64.b64decode(encryption_key)
        else:
            env_key = os.getenv('VAULT_ENCRYPTION_KEY')
            if env_key:
                self.master_key = base64.b64decode(env_key)
            else:
                # Generate a new key (in production, this should be stored securely)
                self.master_key = AESGCM.generate_key(bit_length=256)
                print(f"WARNING: Generated new encryption key. Store this securely: {base64.b64encode(self.master_key).decode()}")
        
        if len(self.master_key) != 32:
            raise ValueError("Encryption key must be 32 bytes (256 bits)")
    
    def _derive_user_key(self, user_id: str) -> bytes:
        """Derive a user-specific encryption key from master key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=user_id.encode('utf-8'),
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(self.master_key)
    
    def _compute_hash(self, data: bytes) -> str:
        """Compute SHA-256 hash of data."""
        return hashlib.sha256(data).hexdigest()
    
    def upload_document(
        self,
        user_id: str,
        document_data: bytes,
        document_type: DocumentType,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProofDocument:
        """
        Upload and encrypt a document.
        
        Args:
            user_id: User identifier
            document_data: Raw document bytes
            document_type: Type of document
            file_name: Original filename
            mime_type: MIME type of document
            metadata: Additional metadata
            
        Returns:
            ProofDocument instance
        """
        # Compute document hash
        doc_hash = self._compute_hash(document_data)
        
        # Generate document ID
        doc_id = f"doc_{user_id}_{int(datetime.utcnow().timestamp() * 1000)}"
        
        # Derive user-specific key
        user_key = self._derive_user_key(user_id)
        
        # Encrypt document
        aesgcm = AESGCM(user_key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        encrypted_data = aesgcm.encrypt(nonce, document_data, None)
        
        # Prepend nonce to encrypted data
        encrypted_with_nonce = nonce + encrypted_data
        
        # Store encrypted file
        file_path = os.path.join(self.storage_path, f"{doc_id}.enc")
        with open(file_path, 'wb') as f:
            f.write(encrypted_with_nonce)
        
        # Create document model
        document = ProofDocument(
            id=doc_id,
            user_id=user_id,
            document_type=document_type,
            encrypted_data=encrypted_with_nonce,
            hash=doc_hash,
            metadata=metadata or {},
            file_name=file_name,
            mime_type=mime_type,
            size_bytes=len(document_data)
        )
        
        # Save metadata as JSON
        meta_path = os.path.join(self.storage_path, f"{doc_id}.meta.json")
        with open(meta_path, 'w') as f:
            json.dump({
                'id': document.id,
                'user_id': document.user_id,
                'document_type': document.document_type.value,
                'hash': document.hash,
                'metadata': document.metadata,
                'created_at': document.created_at.isoformat(),
                'file_name': document.file_name,
                'mime_type': document.mime_type,
                'size_bytes': document.size_bytes
            }, f, indent=2)
        
        return document
    
    def download_document(self, user_id: str, document_id: str) -> bytes:
        """
        Download and decrypt a document.
        
        Args:
            user_id: User identifier (for key derivation)
            document_id: Document identifier
            
        Returns:
            Decrypted document bytes
        """
        file_path = os.path.join(self.storage_path, f"{document_id}.enc")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document {document_id} not found")
        
        # Read encrypted file
        with open(file_path, 'rb') as f:
            encrypted_with_nonce = f.read()
        
        # Extract nonce and encrypted data
        nonce = encrypted_with_nonce[:12]
        encrypted_data = encrypted_with_nonce[12:]
        
        # Derive user-specific key
        user_key = self._derive_user_key(user_id)
        
        # Decrypt document
        aesgcm = AESGCM(user_key)
        decrypted_data = aesgcm.decrypt(nonce, encrypted_data, None)
        
        return decrypted_data
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata without decrypting."""
        meta_path = os.path.join(self.storage_path, f"{document_id}.meta.json")
        if not os.path.exists(meta_path):
            return None
        
        with open(meta_path, 'r') as f:
            return json.load(f)
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its metadata."""
        file_path = os.path.join(self.storage_path, f"{document_id}.enc")
        meta_path = os.path.join(self.storage_path, f"{document_id}.meta.json")
        
        deleted = False
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted = True
        
        if os.path.exists(meta_path):
            os.remove(meta_path)
        
        return deleted

