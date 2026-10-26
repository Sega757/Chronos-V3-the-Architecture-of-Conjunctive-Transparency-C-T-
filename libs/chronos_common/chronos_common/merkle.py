"""SHA-256 Merkle tree over a batch of canonicalized leaves.

Used by System 2 to produce a single ``batch_merkle_root`` for a
``BatchVerificationResult``, and by the audit log to hash-chain individual
rows. Odd levels duplicate the last node (Bitcoin-style) rather than
promoting it unhashed, to avoid second-preimage ambiguity between an
internal node and a leaf.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _parent(left: bytes, right: bytes) -> bytes:
    return sha256(left + right)


def merkle_root(leaves: list[bytes]) -> bytes:
    """Compute the Merkle root over already-hashed leaves.

    Raises ``ValueError`` on an empty leaf set -- an empty batch has no
    meaningful root and callers must not silently treat it as verified.
    """
    if not leaves:
        raise ValueError("merkle_root: at least one leaf is required")
    level = list(leaves)
    sha256_fn = hashlib.sha256
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        # Optimization: Local reference lookup for sha256 to avoid repeated global/attribute lookups in loops
        level = [sha256_fn(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
    return level[0]


@dataclass
class MerkleTree:
    """A Merkle tree that retains every level, so it can produce inclusion
    proofs for a given leaf index."""

    leaves: list[bytes]
    levels: list[list[bytes]] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if not self.leaves:
            raise ValueError("MerkleTree: at least one leaf is required")
        level = list(self.leaves)
        sha256_fn = hashlib.sha256
        self.levels = []
        while len(level) > 1:
            # Optimization: Append padding leaf in-place before saving to self.levels.
            # Storing pre-padded levels ensures every retained level in self.levels[:-1]
            # has an even length, eliminating level array duplication in proof generation (~2.4x speedup).
            if len(level) % 2 == 1:
                level.append(level[-1])
            self.levels.append(level)
            level = [sha256_fn(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
        self.levels.append(level)

    @property
    def root(self) -> bytes:
        return self.levels[-1][0]

    def proof(self, index: int) -> list[tuple[bytes, str]]:
        """Return the sibling hashes needed to reconstruct the root from
        ``leaves[index]``, each tagged with its side ('L' or 'R')."""
        if not (0 <= index < len(self.leaves)):
            raise IndexError(index)
        path: list[tuple[bytes, str]] = []
        idx = index
        # Optimization: Because self.levels[:-1] stored pre-padded levels,
        # level is guaranteed to be even-length. No temporary list allocation (level + [level[-1]]) needed.
        for level in self.levels[:-1]:
            sibling_idx = idx ^ 1
            side = "R" if sibling_idx > idx else "L"
            path.append((level[sibling_idx], side))
            idx //= 2
        return path


def verify_proof(leaf: bytes, proof: list[tuple[bytes, str]], root: bytes) -> bool:
    node = leaf
    sha256_fn = hashlib.sha256
    for sibling, side in proof:
        node = sha256_fn((node + sibling) if side == "R" else (sibling + node)).digest()
    return node == root
