#!/usr/bin/env python3
"""
Key Rotation Demo Script

Demonstrates the encryption key rotation capability for the vault system.
Shows how documents are re-encrypted with a new key while maintaining data integrity.
"""
import os
import sys
import time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vault.storage import VaultStorage
from vault.models import DocumentType


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_step(step_num, description):
    """Print a step in the demo."""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 70)


def demo_key_rotation():
    """Demonstrate key rotation functionality."""

    print_section("ENCRYPTION KEY ROTATION DEMO")
    print("\nThis demo shows how the vault system can rotate encryption keys")
    print("while maintaining data integrity and security.")

    # Setup
    print_step(1, "Initialize Vault with Initial Key")

    # Generate initial key
    initial_key = AESGCM.generate_key(bit_length=256)
    initial_key_b64 = base64.b64encode(initial_key).decode()

    print("✓ Generated initial encryption key")
    print("  Key version: 1")
    print(f"  Key (base64): {initial_key_b64[:32]}...")

    # Create vault with temporary storage
    storage_path = "/tmp/vault_demo_rotation"
    if os.path.exists(storage_path):
        import shutil

        shutil.rmtree(storage_path)

    vault = VaultStorage(encryption_key=initial_key_b64, storage_path=storage_path)
    print(f"✓ Vault initialized at: {storage_path}")
    print(f"  Current key version: {vault.key_version}")

    # Upload test documents
    print_step(2, "Upload Test Documents")

    test_documents = [
        {
            "user_id": "alice@example.com",
            "content": b"Alice's passport - Personal identification document",
            "type": DocumentType.IDENTITY,
            "filename": "passport.pdf",
            "mime_type": "application/pdf",
        },
        {
            "user_id": "alice@example.com",
            "content": b"Driver's license - Valid until 2028",
            "type": DocumentType.LICENSE,
            "filename": "drivers_license.pdf",
            "mime_type": "application/pdf",
        },
        {
            "user_id": "bob@example.com",
            "content": b"Bob's bank statement - Confidential financial data",
            "type": DocumentType.FINANCIAL,
            "filename": "bank_statement.pdf",
            "mime_type": "application/pdf",
        },
        {
            "user_id": "bob@example.com",
            "content": b"University degree - Master of Computer Science",
            "type": DocumentType.CREDENTIAL,
            "filename": "degree.pdf",
            "mime_type": "application/pdf",
        },
    ]

    uploaded_docs = []
    for i, doc_info in enumerate(test_documents, 1):
        doc = vault.upload_document(
            user_id=doc_info["user_id"],
            document_data=doc_info["content"],
            document_type=doc_info["type"],
            file_name=doc_info["filename"],
            mime_type=doc_info["mime_type"],
        )
        uploaded_docs.append((doc.id, doc_info["user_id"], doc_info["content"]))
        print(f"✓ Uploaded document {i}/{len(test_documents)}")
        print(f"  User: {doc_info['user_id']}")
        print(f"  Type: {doc_info['type'].value}")
        print(f"  File: {doc_info['filename']}")
        print(f"  Document ID: {doc.id}")
        print(f"  Hash: {doc.hash[:16]}...")

    print(f"\n✓ Total documents uploaded: {len(uploaded_docs)}")

    # Verify documents can be decrypted
    print_step(3, "Verify Documents Are Encrypted and Accessible")

    for i, (doc_id, user_id, original_content) in enumerate(uploaded_docs, 1):
        decrypted = vault.download_document(user_id, doc_id)
        assert decrypted == original_content
        print(f"✓ Document {i} verified: Can decrypt with current key")

    print(f"\n✓ All {len(uploaded_docs)} documents verified successfully")

    # Show key rotation history before rotation
    print_step(4, "Check Key Rotation History (Before Rotation)")

    history = vault.get_key_rotation_history()
    print(f"Current key version: {vault.key_version}")
    print(f"Rotation count: {history[0]['rotation_count'] if history else 0}")

    # Perform key rotation
    print_step(5, "Perform Key Rotation")

    print("⏳ Rotating encryption key...")
    print("   - Generating new encryption key")
    print("   - Re-encrypting all documents")
    print("   - Updating metadata")

    start_time = time.time()
    rotation_result = vault.rotate_key()
    rotation_duration = time.time() - start_time

    print("\n✓ Key rotation completed successfully!")
    print("\n📊 Rotation Statistics:")
    print(f"  Old key version: {rotation_result['old_version']}")
    print(f"  New key version: {rotation_result['new_version']}")
    print(f"  Documents re-encrypted: {rotation_result['documents_re_encrypted']}")
    print(f"  Errors: {len(rotation_result['errors'])}")
    print(f"  Duration: {rotation_duration:.2f} seconds")
    print(f"  New key (base64): {rotation_result['new_key_b64'][:32]}...")

    if rotation_result["errors"]:
        print("\n⚠️  Errors encountered:")
        for error in rotation_result["errors"]:
            print(f"  - {error}")

    # Verify documents after rotation
    print_step(6, "Verify Data Integrity After Key Rotation")

    print("Verifying all documents can still be decrypted with new key...\n")

    for i, (doc_id, user_id, original_content) in enumerate(uploaded_docs, 1):
        try:
            decrypted = vault.download_document(user_id, doc_id)
            if decrypted == original_content:
                print(f"✓ Document {i}: Data integrity verified")
                print(f"  Original: {original_content[:30].decode('utf-8', errors='ignore')}...")
                print(f"  Decrypted: {decrypted[:30].decode('utf-8', errors='ignore')}...")
                print("  ✓ Match: Perfect data integrity")
            else:
                print(f"✗ Document {i}: Data mismatch!")
                sys.exit(1)
        except Exception as e:
            print(f"✗ Document {i}: Decryption failed - {e}")
            sys.exit(1)

    print(f"\n✓ All {len(uploaded_docs)} documents verified after rotation")
    print("✓ Data integrity maintained: 100%")

    # Check updated metadata
    print_step(7, "Check Updated Metadata")

    sample_doc_id = uploaded_docs[0][0]
    metadata = vault.get_document_metadata(sample_doc_id)

    print("Sample document metadata:")
    print(f"  Document ID: {metadata['id']}")
    print(f"  Key version: {metadata.get('key_version', 'N/A')}")
    print(f"  Last key rotation: {metadata.get('last_key_rotation', 'N/A')}")
    print(f"  Hash: {metadata['hash'][:16]}...")

    # Show key rotation history after rotation
    print_step(8, "Check Key Rotation History (After Rotation)")

    history = vault.get_key_rotation_history()
    print(f"Current key version: {vault.key_version}")
    print(f"Total rotations performed: {history[0]['rotation_count']}")
    print(f"Last rotation: {history[0]['last_rotation']}")

    # Demonstrate multiple rotations
    print_step(9, "Demonstrate Multiple Sequential Rotations")

    print("Performing two more key rotations...\n")

    for i in range(2):
        print(f"Rotation #{i + 2}:")
        result = vault.rotate_key()
        print(f"  ✓ Version: {result['old_version']} → {result['new_version']}")
        print(f"  ✓ Documents re-encrypted: {result['documents_re_encrypted']}")

    # Final verification
    print("\nFinal verification after multiple rotations...")
    for i, (doc_id, user_id, original_content) in enumerate(uploaded_docs, 1):
        decrypted = vault.download_document(user_id, doc_id)
        assert decrypted == original_content
        print(f"✓ Document {i}: Still accessible and intact")

    print(f"\n✓ All documents verified after {vault.key_version - 1} rotations")

    # Summary
    print_section("DEMO SUMMARY")

    print("\n✅ Key Rotation Capabilities Demonstrated:")
    print("   1. Generate new encryption keys")
    print("   2. Re-encrypt all documents with new key")
    print("   3. Maintain perfect data integrity")
    print("   4. Update document metadata with key version")
    print("   5. Track rotation history")
    print("   6. Support multiple sequential rotations")
    print("   7. Handle multiple users transparently")

    print("\n📈 Final Statistics:")
    print("   Initial key version: 1")
    print(f"   Final key version: {vault.key_version}")
    print(f"   Total rotations: {vault.key_version - 1}")
    print(f"   Documents protected: {len(uploaded_docs)}")
    print("   Data integrity: 100%")
    print("   Zero data loss")

    print("\n🔒 Security Benefits:")
    print("   • Limits exposure window for any single key")
    print("   • Reduces impact of potential key compromise")
    print("   • Supports compliance requirements (key rotation policies)")
    print("   • Enables proactive security posture")
    print("   • Maintains backward compatibility during rotation")

    print("\n✅ DEMO COMPLETED SUCCESSFULLY")
    print("   All documents remain accessible and unmodified")
    print("   Key rotation process validated")

    # Cleanup
    print(f"\n🧹 Cleanup: Demo files stored at {storage_path}")
    print("   (Remove directory when done reviewing)")

    return vault, uploaded_docs, rotation_result


if __name__ == "__main__":
    try:
        demo_key_rotation()
        print("\n" + "=" * 70)
        print("  Demo execution completed without errors")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
