import pytest
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


USER_ID = "11111111-1111-4111-8111-111111111111"


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).parents[2]


def _make_engine(url: str):
    engine = create_engine(url)
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys = ON"))
    return engine


@pytest.fixture
def tmp_sqlite_db(tmp_path):
    """Create a temporary SQLite database with all tables and a test user."""
    db_path = tmp_path / "test.db"
    url = f"sqlite+pysqlite:///{db_path}"
    engine = _make_engine(url)

    # Import models before create_all so tables are registered on Base.metadata
    from app.db.base import Base
    import app.db.models.complaint  # noqa: F401
    import app.db.models.workflow  # noqa: F401
    Base.metadata.create_all(engine)

    # Pre-populate the canonical test user
    from app.db.models.complaint import User
    Session = sessionmaker(bind=engine)
    s = Session()
    s.add(User(id=USER_ID, name="Test Agent", role="agent"))
    s.commit()
    s.close()
    engine.dispose()
    return url


@pytest.fixture
def db_session(tmp_sqlite_db):
    """A plain SQLAlchemy session for repository tests (transactional)."""
    engine = _make_engine(tmp_sqlite_db)
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


@pytest.fixture
def settings(tmp_sqlite_db):
    """Provide a test Settings instance with the test database URL."""
    from app.core.config import Settings
    return Settings(
        environment="development",
        database_url=tmp_sqlite_db,
    )


@pytest.fixture
def client(settings):
    """Provide a FastAPI TestClient wired to the test database."""
    from fastapi.testclient import TestClient
    from app.main import create_app

    app = create_app(settings)
    return TestClient(app)
