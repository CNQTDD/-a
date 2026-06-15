from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings

_engine = None
_SessionLocal = None


def get_engine(settings: Settings | None = None):
    global _engine
    if _engine is None:
        if settings is None:
            settings = Settings()
        url = settings.database_url
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(url, connect_args=connect_args)
    return _engine


def get_session_local(settings: Settings | None = None):
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine(settings)
        _SessionLocal = sessionmaker(bind=engine)
    return _SessionLocal


def get_db():
    """FastAPI dependency: yields a DB session."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
