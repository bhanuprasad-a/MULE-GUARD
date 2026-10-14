"""
MuleGuard Central Configuration Module
Manages environment detection, cryptographic key validation, and production security settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# 1. Environment Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
IS_PRODUCTION = (ENVIRONMENT == "production")

# 2. Allowed Origins for CORS
_raw_origins = os.getenv("ALLOWED_ORIGINS", "").strip()
if _raw_origins:
    ALLOWED_ORIGINS = [orig.strip() for orig in _raw_origins.split(",") if orig.strip()]
elif IS_PRODUCTION:
    # Explicit institutional origins in production
    ALLOWED_ORIGINS = [
        "https://guard.muleguard.bank",
        "https://compliance.muleguard.bank",
        "https://admin.muleguard.bank"
    ]
else:
    # Local development origins (no wildcard with credentials)
    ALLOWED_ORIGINS = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:9350",
        "http://127.0.0.1:9351"
    ]

# 3. Session Cookie Security Parameters
COOKIE_SECURE = IS_PRODUCTION
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "lax"
SESSION_COOKIE_NAME = "muleguard_sid"
