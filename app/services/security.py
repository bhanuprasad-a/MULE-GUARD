"""
MuleGuard Cryptographic & Security Services
Argon2id password hashing, AES-256-GCM biometric vector encryption, and session security.
"""

import os
import hashlib
import secrets
import struct
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Initialize Argon2id password hasher with RFC 9106 recommended parameters
# memory_cost=65536 (64MB), time_cost=3, parallelism=4
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

# 256-bit encryption key for biometric vectors (read from env or fallback to stable deterministic master key)
DEFAULT_MASTER_KEY = b"MuleGuard_Bio_Master_Key_2026_!" # 32 bytes
BIO_ENCRYPTION_KEY = os.getenv("MULEGUARD_BIO_KEY", "").encode("utf-8")
if len(BIO_ENCRYPTION_KEY) != 32:
    BIO_ENCRYPTION_KEY = hashlib.sha256(DEFAULT_MASTER_KEY).digest()


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id."""
    return ph.hash(password)


def verify_password(hash_str: str, password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash."""
    try:
        return ph.verify(hash_str, password)
    except (VerifyMismatchError, VerificationError, Exception):
        return False


def encrypt_biometric_vector(vector: list[float]) -> tuple[bytes, bytes, bytes]:
    """
    Encrypts a float vector using AES-256-GCM.
    Returns (ciphertext, nonce, tag). Note that cryptography's AESGCM appends the 16-byte tag
    to the ciphertext, so we split them for clean database storage.
    """
    # Pack vector into binary float32 buffer
    raw_bytes = struct.pack(f"{len(vector)}f", *vector)
    aesgcm = AESGCM(BIO_ENCRYPTION_KEY)
    nonce = os.urandom(12) # 96-bit nonce
    encrypted = aesgcm.encrypt(nonce, raw_bytes, None)
    ciphertext = encrypted[:-16]
    tag = encrypted[-16:]
    return ciphertext, nonce, tag


def decrypt_biometric_vector(ciphertext: bytes, nonce: bytes, tag: bytes, dimension: int = 512) -> list[float]:
    """
    Decrypts an AES-256-GCM encrypted biometric vector and un-packs it into float list.
    """
    aesgcm = AESGCM(BIO_ENCRYPTION_KEY)
    combined = ciphertext + tag
    decrypted_bytes = aesgcm.decrypt(nonce, combined, None)
    vector = list(struct.unpack(f"{dimension}f", decrypted_bytes))
    return vector


def generate_session_token() -> tuple[str, str]:
    """
    Generates a secure 64-character random hex token and its SHA-256 hash.
    Returns: (raw_token, token_hash)
    The raw_token is sent to the client in an HttpOnly cookie.
    The token_hash is stored in the database auth_sessions table.
    """
    raw_token = secrets.token_hex(32) # 256 bits of entropy
    token_hash = hash_session_token(raw_token)
    return raw_token, token_hash


def hash_session_token(raw_token: str) -> str:
    """Computes SHA-256 hash of a session token for constant-time DB lookup."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
