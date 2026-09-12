from fastapi import FastAPI

app = FastAPI(
    title="MuleGuard API",
    description="Backend API for MuleGuard fraud and mule-account detection",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "MuleGuard API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }