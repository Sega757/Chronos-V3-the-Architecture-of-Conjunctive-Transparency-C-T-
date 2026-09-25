"""Ed25519 signing helpers over RFC 8785 canonical JSON payloads.

Every artifact that crosses a trust boundary in SCCS carries a
``chronos.v3.common.Signature``: an Ed25519 signature over the SHA-256
hash of the canonicalized payload, plus the signer's public key and id.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from chronos_common.canonical_json import canonicalize


@dataclass(frozen=True)
class KeyPair:
    node_id: str
    private_key: Ed25519PrivateKey

    @classmethod
    def generate(cls, node_id: str) -> "KeyPair":
        return cls(node_id=node_id, private_key=Ed25519PrivateKey.generate())

    @property
    def public_key_bytes(self) -> bytes:
        return self.private_key.public_key().public_bytes_raw()


@dataclass(frozen=True)
class SignedPayload:
    signer_id: str
    public_key: bytes
    signature: bytes
    payload_hash: bytes


class Ed25519Signer:
    """Signs canonicalized payloads on behalf of a single node identity."""

    def __init__(self, keypair: KeyPair) -> None:
        self._keypair = keypair

    def sign(self, payload: Any) -> SignedPayload:
        canonical = canonicalize(payload)
        digest = hashlib.sha256(canonical).digest()
        signature = self._keypair.private_key.sign(digest)
        return SignedPayload(
            signer_id=self._keypair.node_id,
            public_key=self._keypair.public_key_bytes,
            signature=signature,
            payload_hash=digest,
        )


def verify_signature(payload: Any, public_key: bytes, signature: bytes) -> bool:
    """Verify that ``signature`` is a valid Ed25519 signature by the holder
    of ``public_key`` over the SHA-256 digest of ``payload``'s canonical
    JSON encoding. Never raises for a bad signature -- returns False."""
    digest = hashlib.sha256(canonicalize(payload)).digest()
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, digest)
        return True
    except InvalidSignature:
        return False
