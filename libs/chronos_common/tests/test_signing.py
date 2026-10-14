import pytest
from chronos_common.signing import Ed25519Signer, KeyPair, verify_signature


def test_verify_signature_valid():
    keypair = KeyPair.generate("node-1")
    signer = Ed25519Signer(keypair)
    payload = {"query": "test_query", "candidates": [1, 2, 3]}

    signed = signer.sign(payload)
    assert verify_signature(payload, signed.public_key, signed.signature) is True


def test_verify_signature_invalid_signature_bytes():
    keypair = KeyPair.generate("node-1")
    signer = Ed25519Signer(keypair)
    payload = {"query": "test_query"}

    signed = signer.sign(payload)
    bad_signature = b"x" * 64
    assert verify_signature(payload, signed.public_key, bad_signature) is False


def test_verify_signature_invalid_public_key():
    keypair = KeyPair.generate("node-1")
    signer = Ed25519Signer(keypair)
    payload = {"query": "test_query"}

    signed = signer.sign(payload)
    # Incorrect public key length / value
    assert verify_signature(payload, b"invalid_key_bytes", signed.signature) is False


def test_verify_signature_malformed_types():
    keypair = KeyPair.generate("node-1")
    signer = Ed25519Signer(keypair)
    payload = {"query": "test_query"}

    signed = signer.sign(payload)
    # Non-bytes public key or signature
    assert verify_signature(payload, "not_bytes_key", signed.signature) is False
    assert verify_signature(payload, signed.public_key, 12345) is False
    # Uncanonicalizable payload type
    assert verify_signature(object(), signed.public_key, signed.signature) is False
