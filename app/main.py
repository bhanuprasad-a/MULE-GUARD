from fastapi import FastAPI, HTTPException

from app.db.database import get_connection

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.api.accounts import router as accounts_router
from app.api.risk import router as risk_router
from app.api.alerts import router as alerts_router
from app.api.cases import router as cases_router
from app.api.audit_logs import router as audit_logs_router
from app.api.remaining import router as remaining_router
from app.api.transactions import router as transactions_router
from app.api.auth import router as auth_router


app = FastAPI(
    title="MuleGuard API",
    description="Backend API for MuleGuard fraud and mule-account detection",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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


@app.get("/")
def root():
    return RedirectResponse(url="/frontend/login.html")


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
        print("DATABASE ERROR:", repr(e))
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}",
        )


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend_root")