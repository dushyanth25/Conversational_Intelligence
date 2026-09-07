from fastapi import APIRouter

from storage.postgres.database import engine

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "Application process is alive"}

@router.get("/ready")
def readiness_check():
    try:
        with engine.connect():
            pass
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready", "error": "Database unavailable"}
