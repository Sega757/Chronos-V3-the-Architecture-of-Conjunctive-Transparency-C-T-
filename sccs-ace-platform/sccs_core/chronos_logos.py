import numpy as np
import json
import time
import uuid
import hashlib
import os
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

KEY_FILE = "private_key.pem"

def load_or_generate_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
            )
    else:
        private_key = ed25519.Ed25519PrivateKey.generate()
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(pem)
    return private_key

private_key = load_or_generate_key()
public_key = private_key.public_key()

def compute_huber_loss(residuals, delta=1.35):
    abs_res = np.abs(residuals)
    mask = abs_res <= delta
    return np.where(mask, 0.5 * (residuals ** 2), delta * (abs_res - 0.5 * delta))

def als_irls_sterilize(raw_values, delta=1.35):
    y = np.array(raw_values)
    baseline = np.median(y)

    for _ in range(5):
        residuals = y - baseline
        abs_res = np.abs(residuals)

        weights = np.ones_like(y)
        outlier_mask = abs_res > delta

        safe_res = np.where(abs_res == 0, 1e-8, abs_res)
        weights[outlier_mask] = delta / safe_res[outlier_mask]

        baseline = np.sum(weights * y) / np.sum(weights)

    final_residuals = y - baseline
    huber_loss = np.mean(compute_huber_loss(final_residuals, delta))
    return baseline, huber_loss

def generate_merkle_root(values):
    hashes = [hashlib.sha256(str(v).encode('utf-8')).hexdigest() for v in values]

    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])
        new_hashes = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i+1]
            new_hashes.append(hashlib.sha256(combined.encode('utf-8')).hexdigest())
        hashes = new_hashes

    return hashes[0] if hashes else ""

def canonical_json(obj):
    return json.dumps(obj, separators=(',', ':'), sort_keys=True)

def process_and_sign(session_id, raw_values, delta):
    if not raw_values:
        raise ValueError("Cannot process empty telemetry.")

    baseline, huber_loss = als_irls_sterilize(raw_values, delta)
    merkle_root = generate_merkle_root(raw_values)

    object_id = f"KO_CHRONOS_VERIFIED_{uuid.uuid4().hex[:8].upper()}"
    payload = {
        "object_id": object_id,
        "baseline_value": float(baseline),
        "source": "chronos_logos.py"
    }

    canonical_str = canonical_json(payload)

    payload_hash = hashlib.sha256(canonical_str.encode('utf-8')).digest()
    message_to_sign = merkle_root.encode('utf-8') + payload_hash
    signature = private_key.sign(message_to_sign)

    return {
        "object_id": object_id,
        "timestamp": int(time.time() * 1000),
        "json": canonical_str,
        "huber_residual": float(huber_loss),
        "signal_present": True,
        "signature": signature,
        "merkle_root": merkle_root
    }
