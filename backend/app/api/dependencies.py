from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from app.db.session import get_session_local


def get_db(request: Request) -> Session:
    """FastAPI dependency: returns a DB session using the app-level settings."""
    settings = request.app.state.settings
    SessionLocal = get_session_local(settings)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
