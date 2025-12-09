#!/usr/bin/env python3
"""
Merkle tree construction and proof generation for authenticity circuit tests.
"""
import hashlib
from typing import List, Tuple


def poseidon_hash(left: str, right: str) -> str:
    """Simplified Poseidon hash (for testing - use actual Poseidon in production)."""
    # In production, use circomlib's Poseidon hash
    # This is a placeholder that combines left and right
    combined = f"{left}{right}".encode()
    return hashlib.sha256(combined).hexdigest()


def build_merkle_tree(leaves: List[str], depth: int = 16) -> Tuple[str, List[List[str]]]:
    """
    Build a Merkle tree and return root and all levels.

    Returns:
        (root_hash, tree_levels) where tree_levels[0] is leaves, tree_levels[-1] is root
    """
    # Pad leaves to power of 2
    target_size = 2**depth
    padded_leaves = leaves + ["0" * 64] * (target_size - len(leaves))
    padded_leaves = padded_leaves[:target_size]

    tree_levels = [padded_leaves]
    current_level = padded_leaves

    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else "0" * 64
            parent = poseidon_hash(left, right)
            next_level.append(parent)
        tree_levels.append(next_level)
        current_level = next_level

    root = current_level[0] if current_level else "0" * 64
    return root, tree_levels


def generate_merkle_proof(
    leaf_index: int, tree_levels: List[List[str]], depth: int = 16
) -> Tuple[List[str], List[int]]:
    """
    Generate Merkle proof path for a leaf.

    Returns:
        (path_elements, path_indices) where:
        - path_elements: sibling hashes at each level
        - path_indices: 0 if leaf is left, 1 if leaf is right
    """
    path_elements = []
    path_indices = []

    current_index = leaf_index

    for level in range(depth):
        level_nodes = tree_levels[level]

        # Determine if current node is left (0) or right (1)
        is_right = current_index % 2
        path_indices.append(is_right)

        # Get sibling
        sibling_index = current_index + 1 if is_right == 0 else current_index - 1
        if sibling_index < len(level_nodes):
            path_elements.append(level_nodes[sibling_index])
        else:
            # Pad with zero if sibling doesn't exist
            path_elements.append("0" * 64)

        # Move to parent level
        current_index = current_index // 2

    return path_elements, path_indices


def verify_merkle_proof(
    leaf: str, root: str, path_elements: List[str], path_indices: List[int]
) -> bool:
    """Verify a Merkle proof."""
    current_hash = leaf

    for i, (sibling, is_right) in enumerate(zip(path_elements, path_indices)):
        if is_right == 0:
            # Leaf is on left, sibling on right
            current_hash = poseidon_hash(current_hash, sibling)
        else:
            # Leaf is on right, sibling on left
            current_hash = poseidon_hash(sibling, current_hash)

    return current_hash == root


# Example usage
if __name__ == "__main__":
    # Create a simple Merkle tree
    leaves = [
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "1111111111111111111111111111111111111111111111111111111111111111",
        "2222222222222222222222222222222222222222222222222222222222222222",
        "3333333333333333333333333333333333333333333333333333333333333333",
    ]

    root, tree_levels = build_merkle_tree(leaves, depth=4)
    print(f"Merkle Root: {root}")

    # Generate proof for first leaf
    path_elements, path_indices = generate_merkle_proof(0, tree_levels, depth=4)
    print("\nProof for leaf 0:")
    print(f"  Path elements: {path_elements}")
    print(f"  Path indices: {path_indices}")

    # Verify proof
    leaf = leaves[0]
    is_valid = verify_merkle_proof(leaf, root, path_elements, path_indices)
    print(f"\nProof valid: {is_valid}")
