import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the test database
Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture to provide a database session for a single test function.
    It creates all tables, yields a session, and then drops all tables.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """
    Fixture to provide a TestClient that uses the test database.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    # Override the get_db dependency in the app
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # Clean up the override after the test
    app.dependency_overrides.clear()