import pytest
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set testing environment before importing other modules
os.environ['TESTING'] = 'true'

from server.server import create_app
from server.models.main import Base, Statement
from server.services.database import get_db
from server.settings import DATABASE_PATHS

@pytest.fixture(scope="session")
def test_db_path():
    """Get the test database path."""
    return DATABASE_PATHS['main']

@pytest.fixture(scope="session")
def test_engine(test_db_path):
    """Create test database engine."""
    engine = create_engine(f"sqlite:///{test_db_path}", connect_args={"check_same_thread": False})
    return engine

@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create test session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def test_db(test_engine, test_session_factory):
    """Create a fresh test database for each test."""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = test_session_factory()
    
    try:
        yield session
    finally:
        session.close()
        # Clean up tables after each test
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override."""
    app = create_app()
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture(scope="function")
def temp_upload_dir():
    """Create a temporary directory for file uploads during testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup is handled by tempfile.mkdtemp() context manager
