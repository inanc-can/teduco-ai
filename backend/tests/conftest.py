"""
Pytest configuration and fixtures
"""

import pytest
from typing import Generator
import os
from unittest.mock import MagicMock

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/teduco_test"
os.environ["MOCK_LLM"] = "true"


@pytest.fixture(scope="session")
def test_db():
    """Setup test database"""
    # Create test database schema
    # In a real scenario, you'd create tables here
    yield
    # Cleanup
    pass


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a fresh database session for each test"""
    # Begin transaction
    # Each test gets isolated transaction
    yield
    # Rollback transaction
    pass


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    mock_client = MagicMock()

    # Mock auth methods
    mock_client.auth.get_user.return_value = MagicMock(
        user=MagicMock(id="test-user-id")
    )

    # Mock table operations
    mock_client.table.return_value = mock_client
    mock_client.select.return_value = mock_client
    mock_client.eq.return_value = mock_client
    mock_client.execute.return_value = MagicMock(data=[])

    return mock_client


@pytest.fixture
def mock_openai():
    """Mock OpenAI API for LLM testing"""
    from unittest.mock import Mock

    mock = Mock()
    mock.ChatCompletion.create.return_value = {
        "choices": [
            {"message": {"content": "This is a mocked LLM response."}}
        ],
        "usage": {"total_tokens": 50},
    }
    return mock


@pytest.fixture
def temp_upload_dir(tmp_path):
    """Temporary directory for file uploads during tests"""
    upload_dir = tmp_path / "test_uploads"
    upload_dir.mkdir()
    return upload_dir


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment after each test"""
    yield
    # Cleanup any test artifacts
    pass


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (database, external services)"
    )
    config.addinivalue_line(
        "markers", "rag: RAG pipeline tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (> 1 second)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark slow tests"""
    for item in items:
        # Mark tests with "slow" in name
        if "slow" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
