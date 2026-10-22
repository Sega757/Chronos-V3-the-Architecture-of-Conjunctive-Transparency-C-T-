"""Ed25519 signing helpers over RFC 8785 canonical JSON payloads.

Every artifact that crosses a trust boundary in SCCS carries a
``chronos.v3.common.Signature``: an Ed25519 signature over the SHA-256
hash of the canonicalized payload, plus the signer's public key and id.
"""

from __future__ import annotations

import functools
import hashlib
from dataclasses import dataclass, field
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
    _public_key_bytes: bytes = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        # Optimization: Pre-extract and store public key raw bytes on keypair initialization.
        # This avoids re-instantiating Ed25519PublicKey objects in C/OpenSSL and re-serializing
        # bytes on every payload signing call.
        pub_bytes = self.private_key.public_key().public_bytes_raw()
        object.__setattr__(self, "_public_key_bytes", pub_bytes)

    @classmethod
    def generate(cls, node_id: str) -> "KeyPair":
        return cls(node_id=node_id, private_key=Ed25519PrivateKey.generate())

    @property
    def public_key_bytes(self) -> bytes:
        return self._public_key_bytes


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


@functools.lru_cache(maxsize=1024)
def _get_public_key_from_bytes(public_key_bytes: bytes) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(public_key_bytes)


def verify_signature(payload: Any, public_key: bytes, signature: bytes) -> bool:
    """Verify that ``signature`` is a valid Ed25519 signature by the holder
    of ``public_key`` over the SHA-256 digest of ``payload``'s canonical
    JSON encoding. Never raises for a bad signature -- returns False."""
    try:
        digest = hashlib.sha256(canonicalize(payload)).digest()
        # Optimization: Cache Ed25519PublicKey objects by public_key bytes with LRU cache
        # to avoid re-parsing raw bytes into C OpenSSL key objects on repeated verifications.
        key = _get_public_key_from_bytes(public_key)
        key.verify(signature, digest)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False
