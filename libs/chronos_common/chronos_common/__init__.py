"""Shared primitives for every SCCS / Chronos V3 service.

This package intentionally has no dependency on any single subsystem
(System 1, System 2, or System 0) -- it is the common substrate that lets
those services agree on how bytes are hashed, signed, and canonicalized so
that Conjunctive Transparency (see docs/architecture/02-conjunctive-transparency.md)
holds across process and network boundaries.
"""

from chronos_common.canonical_json import canonicalize
from chronos_common.epistemics import EpistemicState, shannon_entropy, vmf_concentration
from chronos_common.merkle import MerkleTree, merkle_root
from chronos_common.signing import KeyPair, Ed25519Signer, verify_signature

__all__ = [
    "canonicalize",
    "EpistemicState",
    "shannon_entropy",
    "vmf_concentration",
    "MerkleTree",
    "merkle_root",
    "KeyPair",
    "Ed25519Signer",
    "verify_signature",
]
