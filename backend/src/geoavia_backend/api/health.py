"""Health/liveness endpoint."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    """Lightweight liveness probe for start.sh and the dev /health page."""
    return {"status": "ok"}
