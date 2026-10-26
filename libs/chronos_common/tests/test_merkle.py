import hashlib
import pytest

from chronos_common.merkle import MerkleTree, merkle_root, verify_proof


def _hash(s: str) -> bytes:
    return hashlib.sha256(s.encode("utf-8")).digest()


def test_merkle_root_single_leaf():
    leaf = _hash("leaf_0")
    root = merkle_root([leaf])
    assert root == leaf


def test_merkle_root_empty_raises():
    with pytest.raises(ValueError, match="at least one leaf is required"):
        merkle_root([])


def test_merkle_tree_empty_raises():
    with pytest.raises(ValueError, match="at least one leaf is required"):
        MerkleTree([])


def test_merkle_tree_odd_leaves_proof_and_verify():
    leaves = [_hash(f"leaf_{i}") for i in range(5)]
    tree = MerkleTree(leaves)
    root = tree.root
    assert root == merkle_root(leaves)

    for i in range(len(leaves)):
        proof = tree.proof(i)
        assert verify_proof(leaves[i], proof, root)


def test_merkle_tree_even_leaves_proof_and_verify():
    leaves = [_hash(f"leaf_{i}") for i in range(8)]
    tree = MerkleTree(leaves)
    root = tree.root
    assert root == merkle_root(leaves)

    for i in range(len(leaves)):
        proof = tree.proof(i)
        assert verify_proof(leaves[i], proof, root)


def test_merkle_tree_proof_index_out_of_bounds():
    leaves = [_hash(f"leaf_{i}") for i in range(4)]
    tree = MerkleTree(leaves)

    with pytest.raises(IndexError):
        tree.proof(-1)

    with pytest.raises(IndexError):
        tree.proof(4)


def test_merkle_verify_proof_tampered_leaf():
    leaves = [_hash(f"leaf_{i}") for i in range(3)]
    tree = MerkleTree(leaves)
    root = tree.root

    proof = tree.proof(0)
    tampered_leaf = _hash("tampered")
    assert not verify_proof(tampered_leaf, proof, root)
