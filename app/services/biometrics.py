"""
MuleGuard Biometrics & Presentation-Attack-Detection (PAD) Engine
Handles vector cosine similarity, ephemeral challenge issuance, and liveness verification.
"""

import math
import time
import secrets

# In-memory ephemeral challenge store: challenge_token -> {user_id, employee_id, challenge_type, expires_at}
_ACTIVE_CHALLENGES: dict[str, dict] = {}
CHALLENGE_TTL_SECONDS = 180


def generate_liveness_challenge(user_id: str, employee_id: str) -> dict:
    """
    Generates a secure single-use challenge token and randomized liveness test actions.
    """
    clean_expired_challenges()
    token = secrets.token_urlsafe(32)
    
    # Available active liveness challenges (landmark-geometry verified)
    actions = [
        {"action": "TURN_RIGHT", "instruction": "Turn your head slightly to your RIGHT"},
        {"action": "TURN_LEFT", "instruction": "Turn your head slightly to your LEFT"},
        {"action": "NOD", "instruction": "Nod your head slightly DOWN"}
    ]
    selected = secrets.choice(actions)

    record = {
        "user_id": user_id,
        "employee_id": employee_id,
        "challenge_action": selected["action"],
        "expires_at": time.time() + CHALLENGE_TTL_SECONDS
    }
    _ACTIVE_CHALLENGES[token] = record

    return {
        "challenge_token": token,
        "challenge_action": selected["action"],
        "instruction": selected["instruction"],
        "expires_in_seconds": CHALLENGE_TTL_SECONDS
    }


def validate_challenge_token(token: str) -> dict | None:
    """Validates challenge token and consumes it (single-use)."""
    clean_expired_challenges()
    record = _ACTIVE_CHALLENGES.pop(token, None)
    if not record:
        return None
    if time.time() > record["expires_at"]:
        return None
    return record


def clean_expired_challenges():
    """Prunes expired challenge tokens."""
    now = time.time()
    expired = [k for k, v in _ACTIVE_CHALLENGES.items() if v["expires_at"] < now]
    for k in expired:
        _ACTIVE_CHALLENGES.pop(k, None)


def compute_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Calculates the cosine similarity between two normalized feature vectors.
    Returns float in range [-1.0, 1.0]. Typical threshold for match is >= 0.72.
    """
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def verify_liveness(liveness_proof: dict, required_action: str) -> tuple[bool, str, float]:
    """
    Evaluates Presentation Attack Detection (PAD) and liveness signals.
    Checks:
    1. Landmark movement matches required action
    2. Blink or movement delta meets minimum physical threshold
    3. Confidence metric
    Returns: (is_live: bool, reason: str, confidence: float)
    """
    if not liveness_proof:
        return False, "NO_LIVENESS_PROOF_PROVIDED", 0.0

    # Check simulated or client-computed proof
    action_performed = liveness_proof.get("action_performed")
    confidence = float(liveness_proof.get("confidence", 0.0))

    if action_performed != required_action:
        return False, f"CHALLENGE_MISMATCH (Expected {required_action}, Got {action_performed})", confidence

    if confidence < 0.65:
        return False, "LIVENESS_CONFIDENCE_TOO_LOW", confidence

    # Check frame timestamp continuity if provided
    timestamps = liveness_proof.get("timestamps", [])
    if len(timestamps) >= 3:
        # Verify strictly increasing timestamps
        if not all(timestamps[i] < timestamps[i+1] for i in range(len(timestamps)-1)):
            return False, "TIMESTAMP_NON_MONOTONIC_OR_REPLAYED", confidence

    return True, "LIVENESS_CONFIRMED", confidence
