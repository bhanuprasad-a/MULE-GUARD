import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse

from app.db.database import get_connection
from app.core.config import IS_PRODUCTION, ALLOWED_ORIGINS

from app.api.accounts import router as accounts_router
from app.api.risk import router as risk_router
from app.api.alerts import router as alerts_router
from app.api.cases import router as cases_router
from app.api.audit_logs import router as audit_logs_router
from app.api.remaining import router as remaining_router
from app.api.transactions import router as transactions_router
from app.api.auth import router as auth_router
from app.api.internal import router as internal_router
from app.api.filings import router as filings_router


logger = logging.getLogger("muleguard")

app = FastAPI(
    title="MuleGuard API",
    description="Backend API for MuleGuard fraud and mule-account detection",
    version="1.0.0",
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)

MAX_REQUEST_BODY_SIZE = 15 * 1024 * 1024  # 15 MB limit (supports camera frames / FRS enrollment)

CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: blob:; "
    "media-src 'self' blob:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)


# Request payload size guard
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BODY_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request payload too large. Maximum permitted size is 15MB."},
                )
        except ValueError:
            pass
    return await call_next(request)


# Production security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = CSP_POLICY
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
    if request.url.path.startswith("/frontend/") or request.url.path.endswith(".html") or request.url.path.endswith(".js"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    if IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Global exception handler to prevent leaking stack traces or internal implementation details
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


# CORS configuration - explicit origins only, no wildcard with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(accounts_router)
app.include_router(risk_router)
app.include_router(alerts_router)
app.include_router(cases_router)
app.include_router(audit_logs_router)
app.include_router(remaining_router)
app.include_router(transactions_router)
app.include_router(auth_router)
app.include_router(internal_router)
app.include_router(filings_router)


@app.get("/")
def root():
    return RedirectResponse(url="/frontend/login.html")


@app.get("/favicon.ico")
def favicon():
    return FileResponse("assets/MULEGUARD_SYMBOL.png", media_type="image/png")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/db-test")
def db_test():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                result = cur.fetchone()

        return {
            "database": "connected",
            "result": result[0],
        }

    except Exception as e:
        logger.error(f"DATABASE ERROR in /db-test: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Database connection failed",
        )


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend_root")