import pytest
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).parents[2]


@pytest.fixture
def tmp_sqlite_url(tmp_path):
    """Create a temporary SQLite database with foreign-key enforcement."""
    db_path = tmp_path / "test.db"
    url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(url)
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys = ON"))
    from app.db.base import Base

    Base.metadata.create_all(engine)
    yield url
    engine.dispose()


@pytest.fixture
def db_session(tmp_sqlite_url):
    """Provide a transactional SQLite session that rolls back after each test."""
    engine = create_engine(tmp_sqlite_url)
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys = ON"))
    Session = sessionmaker(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for file-based tests."""
    return tmp_path


@pytest.fixture(scope="session")
def settings():
    """Provide a test Settings instance."""
    from app.core.config import Settings
    return Settings(environment="development")


@pytest.fixture
def client(settings):
    """Provide a FastAPI TestClient."""
    from fastapi.testclient import TestClient
    from app.main import create_app

    app = create_app(settings)
    return TestClient(app)
