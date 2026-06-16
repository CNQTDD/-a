from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings

_engine_cache: dict[str, object] = {}


def get_engine(settings: Settings | None = None):
    """Create or return a cached SQLAlchemy engine for the given database URL."""
    if settings is None:
        settings = Settings()
    url = settings.database_url
    key = str(url)
    if key not in _engine_cache:
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine_cache[key] = create_engine(url, connect_args=connect_args)
    return _engine_cache[key]


def get_session_local(settings: Settings | None = None):
    engine = get_engine(settings)
    return sessionmaker(bind=engine)


def get_db():
    """FastAPI dependency: yields a DB session."""
    session_local = get_session_local()
    db = session_local()
    try:
        yield db
    finally:
        db.close()
