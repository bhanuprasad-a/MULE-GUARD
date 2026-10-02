"""
MuleGuard Authentication & RBAC API Router
Endpoints for Stage 1 credential login, Stage 2 biometric & liveness verification,
session lifecycle, and role-based access control.
"""

from typing import Annotated
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends, Cookie
from pydantic import BaseModel, Field

from app.services.auth_service import (
    authenticate_stage1,
    authenticate_stage2_biometrics,
    enroll_employee_face,
    get_user_from_session,
    revoke_session
)
from app.db.init_auth_db import generate_deterministic_vector
from app.services.rate_limiter import check_auth_rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# --- Schemas ---

class Stage1LoginRequest(BaseModel):
    employee_id: str = Field(..., description="Institutional Employee ID, e.g. MG-INV-001")
    password: str = Field(..., description="Argon2id verified employee password")


class LivenessProof(BaseModel):
    action_performed: str = Field(..., description="Action completed, e.g. BLINK, TURN_HEAD, NOD")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    timestamps: list[float] = Field(default_factory=list)


class Stage2BiometricRequest(BaseModel):
    challenge_token: str = Field(..., description="Ephemeral token issued in Stage 1")
    image_base64: str | None = Field(default=None, description="Base64 encoded live camera JPEG/PNG frame")
    baseline_image_base64: str | None = Field(default=None, description="Base64 encoded baseline neutral camera frame")
    frames: list[str] | None = Field(default=None, description="Sequence of camera frames [baseline, action]")
    probe_vector: list[float] | None = Field(default=None, description="Precomputed biometric face vector (legacy/test)")
    liveness_proof: LivenessProof | None = Field(default=None, description="Presentation attack detection data")


class EnrollFaceRequest(BaseModel):
    employee_id: str = Field(..., description="Institutional Employee ID, e.g. MG-INV-001")
    password: str = Field(..., description="Argon2id verified employee password")
    image_base64: str = Field(..., description="Base64 encoded JPEG/PNG frame captured from camera")
    target_all_roles: bool | None = Field(default=False, description="If true, enroll face for all three institutional personas")


class DemoVectorRequest(BaseModel):
    employee_id: str
    noise_level: float = Field(default=0.0, ge=0.0, le=1.0, description="0.0 for exact match, >0.5 for mismatch")


# --- RBAC Dependencies ---

def get_current_user(
    request: Request,
    muleguard_sid: Annotated[str | None, Cookie()] = None
) -> dict:
    """
    Validates the session token from HttpOnly cookie or Authorization Bearer header.
    Returns authenticated user payload or raises HTTP 401.
    """
    token = muleguard_sid
    if not token:
        # Check Authorization header fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. No active session found."
        )

    user = get_user_from_session(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or been revoked. Please re-authenticate."
        )

    return user


def require_role(allowed_roles: list[str]):
    """Returns a dependency that asserts the user holds one of the allowed roles."""
    def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}, current role: {user.get('role')}"
            )
        return user
    return role_checker


# --- API Routes ---

@router.post("/stage1-login", dependencies=[Depends(check_auth_rate_limit)])
def login_stage1(req: Stage1LoginRequest, request: Request):
    """
    Stage 1: Verify Employee ID & Argon2id Password.
    Returns liveness challenge if credentials are valid.
    """
    ip = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("user-agent", "")
    result = authenticate_stage1(req.employee_id, req.password, ip, ua)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("error", "Authentication failed.")
        )

    return result


@router.post("/stage2-verify-face", dependencies=[Depends(check_auth_rate_limit)])
def verify_face_stage2(req: Stage2BiometricRequest, request: Request, response: Response):
    """
    Stage 2: Verify passive PAD, active liveness challenge, and biometric cosine similarity.
    Accepts live camera image sequence, baseline/action pair, single image, or probe vector.
    Issues secure HttpOnly session cookie on success.
    """
    ip = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("user-agent", "")
    liveness_dict = req.liveness_proof.model_dump() if req.liveness_proof else None
    result = authenticate_stage2_biometrics(
        challenge_token=req.challenge_token,
        probe_vector=req.probe_vector,
        image_base64=req.image_base64,
        baseline_image_base64=req.baseline_image_base64,
        frames=req.frames,
        liveness_proof=liveness_dict,
        ip_address=ip,
        user_agent=ua
    )

    if not result.get("success"):
        err_code = result.get("code")
        if err_code in ["FACE_DETECTION_FAILED", "PRESENTATION_ATTACK_DETECTED", "LIVENESS_FAILED"]:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_401_UNAUTHORIZED

        raise HTTPException(
            status_code=status_code,
            detail=result.get("error", "Biometric verification failed.")
        )

    # Set secure HttpOnly session cookie
    session_token = result.pop("session_token")
    response.set_cookie(
        key="muleguard_sid",
        value=session_token,
        max_age=8 * 3600, # 8 hours
        httponly=True,
        samesite="lax",
        secure=False # Set to True in production with HTTPS
    )

    return result


@router.post("/enroll-face", dependencies=[Depends(check_auth_rate_limit)])
def enroll_face(req: EnrollFaceRequest, request: Request):
    """
    Enrolls or updates a real face biometric template for an employee using camera capture.
    Requires password verification and extracts a 128-d SFace embedding.
    If target_all_roles is True, enrolls the face for all institutional personas (MG-ADM-001, MG-INV-001, MG-CMP-001).
    """
    ip = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("user-agent", "")

    if req.target_all_roles:
        results = []
        target_ids = ["MG-ADM-001", "MG-INV-001", "MG-CMP-001"]
        for target_id in target_ids:
            res = enroll_employee_face(
                employee_id=target_id,
                password=req.password,
                image_base64=req.image_base64,
                ip_address=ip,
                user_agent=ua
            )
            results.append({"employee_id": target_id, "result": res})

        primary_res = next((r["result"] for r in results if r["employee_id"] == req.employee_id), results[0]["result"])
        if not primary_res.get("success"):
            status_code = status.HTTP_400_BAD_REQUEST if primary_res.get("code") == "FACE_DETECTION_FAILED" else status.HTTP_401_UNAUTHORIZED
            raise HTTPException(
                status_code=status_code,
                detail=primary_res.get("error", "Face enrollment failed.")
            )

        return {
            "success": True,
            "message": "Biometric face template enrolled successfully for all 3 logins (Internal Team, Investigator, Compliance)!",
            "algorithm": primary_res.get("algorithm", "opencv-sface-128"),
            "embedding_dimension": primary_res.get("embedding_dimension", 128),
            "quality_score": primary_res.get("quality_score", 95.0),
            "enrolled_accounts": target_ids
        }

    result = enroll_employee_face(
        employee_id=req.employee_id,
        password=req.password,
        image_base64=req.image_base64,
        ip_address=ip,
        user_agent=ua
    )

    if not result.get("success"):
        status_code = status.HTTP_400_BAD_REQUEST if result.get("code") == "FACE_DETECTION_FAILED" else status.HTTP_401_UNAUTHORIZED
        raise HTTPException(
            status_code=status_code,
            detail=result.get("error", "Face enrollment failed.")
        )

    return result



@router.get("/me")
def get_current_user_profile(user: dict = Depends(get_current_user)):
    """Returns profile and role of currently authenticated session."""
    return {"authenticated": True, "user": user}


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    muleguard_sid: Annotated[str | None, Cookie()] = None
):
    """Revokes session and clears session cookie."""
    token = muleguard_sid
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if token:
        ip = request.client.host if request.client else "127.0.0.1"
        ua = request.headers.get("user-agent", "")
        revoke_session(token, ip, ua)

    response.delete_cookie(key="muleguard_sid")
    return {"success": True, "message": "Successfully logged out."}


@router.post("/demo-probe-vector")
def get_demo_probe_vector(req: DemoVectorRequest):
    """
    Helper for browser demo and automated testing to produce a normalized
    biometric vector matching the enrolled template for an employee.
    If noise_level > 0, introduces variance to simulate mismatch or low quality.
    """
    clean_id = req.employee_id.strip()
    base_vec = None

    # Check if user has enrolled real template in DB
    try:
        from app.db.database import get_connection
        from psycopg.rows import dict_row
        from app.services.security import decrypt_biometric_vector
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT b.encrypted_embedding, b.encryption_nonce, b.encryption_tag, b.embedding_dimension
                    FROM auth_biometric_credentials b
                    JOIN auth_users u ON u.id = b.user_id
                    WHERE u.employee_id = %s AND b.status = 'ACTIVE';
                    """,
                    (clean_id,)
                )
                row = cur.fetchone()
                if row:
                    base_vec = decrypt_biometric_vector(
                        bytes(row["encrypted_embedding"]),
                        bytes(row["encryption_nonce"]),
                        bytes(row["encryption_tag"]),
                        dimension=row["embedding_dimension"]
                    )
    except Exception:
        base_vec = None

    if not base_vec:
        base_vec = generate_deterministic_vector(clean_id)

    if req.noise_level > 0.0:
        import random
        import math
        rng = random.Random(42)
        noise = [rng.gauss(0, 1) for _ in base_vec]
        mixed = [(1.0 - req.noise_level) * b + req.noise_level * n for b, n in zip(base_vec, noise)]
        norm = math.sqrt(sum(x * x for x in mixed))
        probe = [x / norm for x in mixed]
    else:
        probe = base_vec

    return {
        "employee_id": req.employee_id,
        "dimension": len(probe),
        "probe_vector": probe
    }


@router.get("/demo-sample-face")
def get_demo_sample_face():
    """
    Returns a base64 encoded face photo for one-click testing and demonstration.
    """
    import os
    import base64
    candidate_paths = [
        os.path.join("data", "models", "face1.jpg"),
        os.path.join("data", "models", "messi_face.jpg"),
        os.path.join("data", "models", "charlie.jpg")
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return {
                    "success": True,
                    "image_base64": f"data:image/jpeg;base64,{b64}",
                    "filename": os.path.basename(p)
                }
    return {"success": False, "error": "Sample image not found on server"}

