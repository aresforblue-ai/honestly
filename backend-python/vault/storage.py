"""
Encrypted storage service for vault documents using AES-256-GCM.
Supports key rotation and versioning for security compliance.
"""
import os
import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import logging

from vault.models import ProofDocument, DocumentType

logger = logging.getLogger(__name__)


class VaultStorage:
    """Encrypted storage service for vault documents with key rotation support."""
    
    def __init__(self, encryption_key: Optional[str] = None, storage_path: str = "vault_storage"):
        """
        Initialize vault storage.
        
        Args:
            encryption_key: Base64-encoded encryption key. If None, generates from env or creates new.
            storage_path: Directory path for storing encrypted files.
        """
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        # Initialize key versioning
        self.key_version = 1
        self.key_history: Dict[int, bytes] = {}
        
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
                logger.warning("Generated new encryption key. Set VAULT_ENCRYPTION_KEY environment variable to persist it.")
        
        if len(self.master_key) != 32:
            raise ValueError("Encryption key must be 32 bytes (256 bits)")
        
        # Store current key in history
        self.key_history[self.key_version] = self.master_key
        
        # Load key version metadata if exists
        self._load_key_metadata()
    
    def _derive_user_key(self, user_id: str) -> bytes:
        """Derive a user-specific encryption key from master key."""
        return self._derive_user_key_from_master(user_id, self.master_key)
    
    def _derive_user_key_from_master(self, user_id: str, master_key: bytes) -> bytes:
        """Derive a user-specific encryption key from a specific master key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=user_id.encode('utf-8'),
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(master_key)
    
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
    
    def _load_key_metadata(self) -> None:
        """Load key version metadata from storage."""
        key_meta_path = os.path.join(self.storage_path, "key_metadata.json")
        if os.path.exists(key_meta_path):
            try:
                with open(key_meta_path, 'r') as f:
                    meta = json.load(f)
                    self.key_version = meta.get('current_version', 1)
                    logger.info(f"Loaded key metadata, current version: {self.key_version}")
            except Exception as e:
                logger.error(f"Error loading key metadata: {e}")
    
    def _save_key_metadata(self) -> None:
        """Save key version metadata to storage."""
        key_meta_path = os.path.join(self.storage_path, "key_metadata.json")
        try:
            with open(key_meta_path, 'w') as f:
                json.dump({
                    'current_version': self.key_version,
                    'last_rotation': datetime.utcnow().isoformat(),
                    'rotation_count': len(self.key_history) - 1
                }, f, indent=2)
            logger.info(f"Saved key metadata, version: {self.key_version}")
        except Exception as e:
            logger.error(f"Error saving key metadata: {e}")
    
    def rotate_key(self, new_key: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Rotate the master encryption key and re-encrypt all documents.
        
        Args:
            new_key: Optional new key. If None, generates a new one.
            
        Returns:
            Dictionary with rotation results including stats and new key.
        """
        # Generate or validate new key
        if new_key is None:
            new_key = AESGCM.generate_key(bit_length=256)
        elif len(new_key) != 32:
            raise ValueError("New key must be 32 bytes (256 bits)")
        
        # Store old key version
        old_version = self.key_version
        old_key = self.master_key
        
        # Update to new key
        new_version = old_version + 1
        self.key_version = new_version
        self.master_key = new_key
        self.key_history[new_version] = new_key
        
        # Re-encrypt all documents
        stats = {
            'old_version': old_version,
            'new_version': new_version,
            'documents_re_encrypted': 0,
            'errors': [],
            'start_time': datetime.utcnow().isoformat()
        }
        
        # Find all encrypted documents
        for filename in os.listdir(self.storage_path):
            if not filename.endswith('.enc'):
                continue
            
            doc_id = filename.replace('.enc', '')
            try:
                # Get document metadata
                metadata = self.get_document_metadata(doc_id)
                if not metadata:
                    continue
                
                user_id = metadata['user_id']
                
                # Decrypt with old key (derive old user key directly)
                old_user_key = self._derive_user_key_from_master(user_id, old_key)
                file_path = os.path.join(self.storage_path, f"{doc_id}.enc")
                with open(file_path, 'rb') as f:
                    encrypted_with_nonce = f.read()
                
                nonce_old = encrypted_with_nonce[:12]
                encrypted_data_old = encrypted_with_nonce[12:]
                aesgcm_old = AESGCM(old_user_key)
                decrypted_data = aesgcm_old.decrypt(nonce_old, encrypted_data_old, None)
                
                # Re-encrypt with new key
                user_key = self._derive_user_key(user_id)  # Uses current master_key (new_key)
                aesgcm = AESGCM(user_key)
                nonce = os.urandom(12)
                encrypted_data = aesgcm.encrypt(nonce, decrypted_data, None)
                encrypted_with_nonce = nonce + encrypted_data
                
                # Save re-encrypted document
                file_path = os.path.join(self.storage_path, f"{doc_id}.enc")
                with open(file_path, 'wb') as f:
                    f.write(encrypted_with_nonce)
                
                # Update metadata with key version
                metadata['key_version'] = new_version
                metadata['last_key_rotation'] = datetime.utcnow().isoformat()
                meta_path = os.path.join(self.storage_path, f"{doc_id}.meta.json")
                with open(meta_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                stats['documents_re_encrypted'] += 1
                
            except Exception as e:
                error_msg = f"Error re-encrypting {doc_id}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        # Save key metadata
        self._save_key_metadata()
        
        stats['end_time'] = datetime.utcnow().isoformat()
        stats['new_key_b64'] = base64.b64encode(new_key).decode()
        
        logger.info(f"Key rotation complete: {stats['documents_re_encrypted']} documents re-encrypted")
        return stats
    
    def get_key_rotation_history(self) -> List[Dict[str, Any]]:
        """Get the history of key rotations."""
        key_meta_path = os.path.join(self.storage_path, "key_metadata.json")
        if not os.path.exists(key_meta_path):
            return []
        
        with open(key_meta_path, 'r') as f:
            meta = json.load(f)
            return [{
                'current_version': meta.get('current_version'),
                'last_rotation': meta.get('last_rotation'),
                'rotation_count': meta.get('rotation_count', 0)
            }]

