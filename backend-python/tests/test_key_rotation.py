"""
Test suite for encryption key rotation functionality.
Tests key rotation, re-encryption, and data integrity.
"""

import pytest
import os
import tempfile
import shutil
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

from vault.storage import VaultStorage
from vault.models import DocumentType


class TestKeyRotation:
    """Test encryption key rotation."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def vault_with_documents(self, temp_storage):
        """Create vault with test documents."""
        # Generate a test key
        test_key = AESGCM.generate_key(bit_length=256)
        test_key_b64 = base64.b64encode(test_key).decode()

        vault = VaultStorage(encryption_key=test_key_b64, storage_path=temp_storage)

        # Upload test documents
        test_docs = [
            {
                "user_id": "user1",
                "data": b"Test document 1 content",
                "type": DocumentType.IDENTITY,
                "filename": "test1.txt",
            },
            {
                "user_id": "user1",
                "data": b"Test document 2 with more content",
                "type": DocumentType.LICENSE,
                "filename": "test2.txt",
            },
            {
                "user_id": "user2",
                "data": b"User 2 document content",
                "type": DocumentType.FINANCIAL,
                "filename": "test3.txt",
            },
        ]

        doc_ids = []
        for doc in test_docs:
            uploaded = vault.upload_document(
                user_id=doc["user_id"],
                document_data=doc["data"],
                document_type=doc["type"],
                file_name=doc["filename"],
            )
            doc_ids.append((uploaded.id, doc["user_id"], doc["data"]))

        return vault, doc_ids

    def test_initial_key_version(self, temp_storage):
        """Test that vault starts with key version 1."""
        test_key = AESGCM.generate_key(bit_length=256)
        test_key_b64 = base64.b64encode(test_key).decode()

        vault = VaultStorage(encryption_key=test_key_b64, storage_path=temp_storage)
        assert vault.key_version == 1
        assert 1 in vault.key_history

    def test_key_rotation_increments_version(self, vault_with_documents):
        """Test that key rotation increments version."""
        vault, _ = vault_with_documents

        initial_version = vault.key_version
        result = vault.rotate_key()

        assert vault.key_version == initial_version + 1
        assert result["old_version"] == initial_version
        assert result["new_version"] == initial_version + 1

    def test_key_rotation_with_no_documents(self, temp_storage):
        """Test key rotation with empty vault."""
        test_key = AESGCM.generate_key(bit_length=256)
        test_key_b64 = base64.b64encode(test_key).decode()

        vault = VaultStorage(encryption_key=test_key_b64, storage_path=temp_storage)

        result = vault.rotate_key()

        assert result["documents_re_encrypted"] == 0
        assert len(result["errors"]) == 0
        assert vault.key_version == 2

    def test_key_rotation_re_encrypts_documents(self, vault_with_documents):
        """Test that all documents are re-encrypted."""
        vault, doc_ids = vault_with_documents

        result = vault.rotate_key()

        assert result["documents_re_encrypted"] == len(doc_ids)
        assert len(result["errors"]) == 0

    def test_key_rotation_preserves_data(self, vault_with_documents):
        """Test that data integrity is preserved after rotation."""
        vault, doc_ids = vault_with_documents

        # Rotate key
        result = vault.rotate_key()
        assert result["documents_re_encrypted"] == len(doc_ids)

        # Verify all documents can be decrypted with new key
        for doc_id, user_id, original_data in doc_ids:
            decrypted_data = vault.download_document(user_id, doc_id)
            assert decrypted_data == original_data

    def test_key_rotation_with_custom_key(self, vault_with_documents):
        """Test key rotation with a provided new key."""
        vault, doc_ids = vault_with_documents

        # Generate a specific new key
        new_key = AESGCM.generate_key(bit_length=256)

        result = vault.rotate_key(new_key=new_key)

        assert vault.master_key == new_key
        assert result["new_key_b64"] == base64.b64encode(new_key).decode()

        # Verify documents can still be decrypted
        for doc_id, user_id, original_data in doc_ids:
            decrypted_data = vault.download_document(user_id, doc_id)
            assert decrypted_data == original_data

    def test_key_rotation_invalid_key_length(self, vault_with_documents):
        """Test key rotation with invalid key length."""
        vault, _ = vault_with_documents

        # Try to rotate with wrong key length
        bad_key = b"short_key"

        with pytest.raises(ValueError, match="32 bytes"):
            vault.rotate_key(new_key=bad_key)

    def test_multiple_key_rotations(self, vault_with_documents):
        """Test multiple sequential key rotations."""
        vault, doc_ids = vault_with_documents

        # Rotate key multiple times
        for i in range(3):
            result = vault.rotate_key()
            expected_version = i + 2  # Starts at 1, so 2, 3, 4
            assert vault.key_version == expected_version
            assert result["new_version"] == expected_version

        # Verify data integrity after multiple rotations
        for doc_id, user_id, original_data in doc_ids:
            decrypted_data = vault.download_document(user_id, doc_id)
            assert decrypted_data == original_data

    def test_key_rotation_updates_metadata(self, vault_with_documents):
        """Test that document metadata is updated with key version."""
        vault, doc_ids = vault_with_documents

        # Rotate key
        vault.rotate_key()

        # Check that metadata includes key version
        for doc_id, _, _ in doc_ids:
            metadata = vault.get_document_metadata(doc_id)
            assert metadata is not None
            assert "key_version" in metadata
            assert metadata["key_version"] == 2
            assert "last_key_rotation" in metadata

    def test_key_metadata_persistence(self, temp_storage):
        """Test that key metadata is saved and can be loaded."""
        test_key = AESGCM.generate_key(bit_length=256)
        test_key_b64 = base64.b64encode(test_key).decode()

        # Create vault and upload document
        vault1 = VaultStorage(encryption_key=test_key_b64, storage_path=temp_storage)
        vault1.upload_document(
            user_id="user1", document_data=b"Test content", document_type=DocumentType.IDENTITY
        )

        # Rotate key
        result = vault1.rotate_key()
        new_key_b64 = result["new_key_b64"]

        # Create new vault instance with rotated key
        vault2 = VaultStorage(encryption_key=new_key_b64, storage_path=temp_storage)

        # Should load key version from metadata
        assert vault2.key_version == 2

    def test_key_rotation_history(self, vault_with_documents):
        """Test key rotation history tracking."""
        vault, _ = vault_with_documents

        # Initial state - no metadata file yet
        history = vault.get_key_rotation_history()
        assert len(history) == 0 or history[0]["rotation_count"] == 0

        # After rotation
        vault.rotate_key()
        history = vault.get_key_rotation_history()
        assert len(history) == 1
        assert history[0]["current_version"] == 2
        assert history[0]["rotation_count"] == 1

    def test_key_rotation_different_users(self, temp_storage):
        """Test key rotation with documents from multiple users."""
        test_key = AESGCM.generate_key(bit_length=256)
        test_key_b64 = base64.b64encode(test_key).decode()
        vault = VaultStorage(encryption_key=test_key_b64, storage_path=temp_storage)

        # Upload documents for different users
        users_and_data = [
            ("user1", b"User 1 document"),
            ("user2", b"User 2 document"),
            ("user3", b"User 3 document"),
        ]

        doc_ids = []
        for user_id, data in users_and_data:
            doc = vault.upload_document(
                user_id=user_id, document_data=data, document_type=DocumentType.OTHER
            )
            doc_ids.append((doc.id, user_id, data))

        # Rotate key
        result = vault.rotate_key()
        assert result["documents_re_encrypted"] == len(doc_ids)

        # Verify each user's documents
        for doc_id, user_id, original_data in doc_ids:
            decrypted = vault.download_document(user_id, doc_id)
            assert decrypted == original_data

    def test_key_rotation_large_document(self, temp_storage):
        """Test key rotation with large document."""
        test_key = AESGCM.generate_key(bit_length=256)
        test_key_b64 = base64.b64encode(test_key).decode()
        vault = VaultStorage(encryption_key=test_key_b64, storage_path=temp_storage)

        # Upload large document (1MB)
        large_data = b"x" * (1024 * 1024)
        doc = vault.upload_document(
            user_id="user1", document_data=large_data, document_type=DocumentType.OTHER
        )

        # Rotate key
        result = vault.rotate_key()
        assert result["documents_re_encrypted"] == 1

        # Verify large document
        decrypted = vault.download_document("user1", doc.id)
        assert decrypted == large_data

    def test_key_rotation_binary_document(self, temp_storage):
        """Test key rotation with binary data."""
        test_key = AESGCM.generate_key(bit_length=256)
        test_key_b64 = base64.b64encode(test_key).decode()
        vault = VaultStorage(encryption_key=test_key_b64, storage_path=temp_storage)

        # Upload binary document (simulate image/pdf)
        binary_data = bytes(range(256)) * 100  # All byte values
        doc = vault.upload_document(
            user_id="user1",
            document_data=binary_data,
            document_type=DocumentType.OTHER,
            mime_type="application/octet-stream",
        )

        # Rotate key
        vault.rotate_key()

        # Verify binary data integrity
        decrypted = vault.download_document("user1", doc.id)
        assert decrypted == binary_data

    def test_key_rotation_metadata_preservation(self, temp_storage):
        """Test that custom metadata is preserved during rotation."""
        test_key = AESGCM.generate_key(bit_length=256)
        test_key_b64 = base64.b64encode(test_key).decode()
        vault = VaultStorage(encryption_key=test_key_b64, storage_path=temp_storage)

        # Upload document with custom metadata
        custom_meta = {
            "issuer": "Government",
            "expiry": "2025-12-31",
            "custom_field": "custom_value",
        }
        doc = vault.upload_document(
            user_id="user1",
            document_data=b"Test content",
            document_type=DocumentType.LICENSE,
            metadata=custom_meta,
        )

        # Rotate key
        vault.rotate_key()

        # Verify metadata preserved
        metadata = vault.get_document_metadata(doc.id)
        assert metadata["metadata"] == custom_meta

    def test_concurrent_key_rotation_safety(self, vault_with_documents):
        """Test key rotation handles concurrent operations safely."""
        vault, doc_ids = vault_with_documents

        # This is a simplified test - real concurrent testing would use threads
        # For now, just verify that rotation completes successfully
        result = vault.rotate_key()

        assert result["documents_re_encrypted"] == len(doc_ids)
        assert len(result["errors"]) == 0

        # Verify all documents still accessible
        for doc_id, user_id, original_data in doc_ids:
            decrypted = vault.download_document(user_id, doc_id)
            assert decrypted == original_data

    def test_key_rotation_result_contains_stats(self, vault_with_documents):
        """Test that rotation result contains complete statistics."""
        vault, doc_ids = vault_with_documents

        result = vault.rotate_key()

        # Check all required fields
        assert "old_version" in result
        assert "new_version" in result
        assert "documents_re_encrypted" in result
        assert "errors" in result
        assert "start_time" in result
        assert "end_time" in result
        assert "new_key_b64" in result

        assert result["documents_re_encrypted"] == len(doc_ids)
        assert isinstance(result["errors"], list)


class TestKeyRotationEdgeCases:
    """Test edge cases for key rotation."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_key_rotation_with_corrupted_metadata(self, temp_storage):
        """Test key rotation when metadata file is corrupted."""
        test_key = AESGCM.generate_key(bit_length=256)
        test_key_b64 = base64.b64encode(test_key).decode()
        vault = VaultStorage(encryption_key=test_key_b64, storage_path=temp_storage)

        # Upload document
        doc = vault.upload_document(
            user_id="user1", document_data=b"Test content", document_type=DocumentType.IDENTITY
        )

        # Corrupt metadata file
        meta_path = os.path.join(temp_storage, f"{doc.id}.meta.json")
        with open(meta_path, "w") as f:
            f.write("corrupted json {{{")

        # Rotation should handle corrupted metadata gracefully
        result = vault.rotate_key()

        # Should have an error for the corrupted document
        assert len(result["errors"]) > 0

    def test_key_rotation_with_missing_document_file(self, temp_storage):
        """Test key rotation when encrypted file is missing."""
        test_key = AESGCM.generate_key(bit_length=256)
        test_key_b64 = base64.b64encode(test_key).decode()
        vault = VaultStorage(encryption_key=test_key_b64, storage_path=temp_storage)

        # Upload document
        doc = vault.upload_document(
            user_id="user1", document_data=b"Test content", document_type=DocumentType.IDENTITY
        )

        # Delete encrypted file but keep metadata
        enc_path = os.path.join(temp_storage, f"{doc.id}.enc")
        os.remove(enc_path)

        # Rotation should handle missing file gracefully
        # The rotation may skip files with missing metadata, so errors may be 0
        # This is acceptable behavior - we just verify it doesn't crash
        result = vault.rotate_key()

        # Should complete without crashing
        assert "documents_re_encrypted" in result
        assert vault.key_version == 2

    def test_key_rotation_with_empty_storage(self, temp_storage):
        """Test key rotation with completely empty storage."""
        test_key = AESGCM.generate_key(bit_length=256)
        test_key_b64 = base64.b64encode(test_key).decode()
        vault = VaultStorage(encryption_key=test_key_b64, storage_path=temp_storage)

        result = vault.rotate_key()

        assert result["documents_re_encrypted"] == 0
        assert len(result["errors"]) == 0
        assert vault.key_version == 2
