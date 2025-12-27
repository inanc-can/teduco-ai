"""
Test utilities and helpers for backend tests
"""

from typing import Dict, Any, Optional
from unittest.mock import MagicMock
import jwt
from datetime import datetime, timedelta


def create_mock_jwt_token(user_id: str = "test-user-123", exp_minutes: int = 60) -> str:
    """
    Create a mock JWT token for testing

    Args:
        user_id: User ID to include in token
        exp_minutes: Expiration time in minutes

    Returns:
        Mock JWT token string
    """
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=exp_minutes),
        "iat": datetime.utcnow(),
    }
    # Use a test secret - this is only for testing!
    return jwt.encode(payload, "test-secret", algorithm="HS256")


def create_mock_supabase_response(data: Any, error: Optional[str] = None):
    """
    Create a mock Supabase response object

    Args:
        data: Response data
        error: Error message if any

    Returns:
        Mock response object
    """
    response = MagicMock()
    response.data = data
    response.error = error
    return response


def create_auth_headers(user_id: str = "test-user-123") -> Dict[str, str]:
    """
    Create authorization headers for testing

    Args:
        user_id: User ID to include in token

    Returns:
        Dictionary with Authorization header
    """
    token = create_mock_jwt_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def assert_camelcase_response(response_data: Dict[str, Any]):
    """
    Assert that response uses camelCase (not snake_case)

    Args:
        response_data: Response dictionary to check
    """
    for key in response_data.keys():
        # Check that key is camelCase (no underscores except private fields)
        if not key.startswith("_"):
            assert "_" not in key, f"Found snake_case key '{key}' in response"


def create_mock_file(filename: str = "test.pdf", content: bytes = b"test content"):
    """
    Create a mock file for upload testing

    Args:
        filename: Name of the file
        content: File content

    Returns:
        Mock file object
    """
    from io import BytesIO

    file_obj = BytesIO(content)
    file_obj.name = filename
    return file_obj


class MockSupabaseClient:
    """
    Mock Supabase client for testing
    """

    def __init__(self):
        self.auth = MagicMock()
        self._table_name = None
        self._query_data = []

    def table(self, name: str):
        """Mock table selection"""
        self._table_name = name
        return self

    def select(self, *args, **kwargs):
        """Mock select query"""
        return self

    def insert(self, data):
        """Mock insert query"""
        self._query_data.append(data)
        return self

    def update(self, data):
        """Mock update query"""
        return self

    def upsert(self, data):
        """Mock upsert query"""
        return self

    def delete(self):
        """Mock delete query"""
        return self

    def eq(self, column, value):
        """Mock equality filter"""
        return self

    def execute(self):
        """Mock query execution"""
        return create_mock_supabase_response(self._query_data)


def seed_test_database():
    """
    Seed test database with sample data
    This is a placeholder - implement based on your database setup
    """
    # TODO: Implement database seeding
    pass


def cleanup_test_database():
    """
    Clean up test database after tests
    This is a placeholder - implement based on your database setup
    """
    # TODO: Implement database cleanup
    pass


# Sample data generators
def generate_mock_user_data(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate mock user profile data"""
    return {
        "id": user_id or "user-123-456-789",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "created_at": datetime.utcnow().isoformat(),
    }


def generate_mock_document_data(doc_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate mock document data"""
    return {
        "document_id": doc_id or "doc-123-456",
        "user_id": "user-123-456-789",
        "file_name": "test.pdf",
        "file_size": 102400,
        "doc_type": "transcript",
        "upload_path": "uploads/test.pdf",
        "uploaded_at": datetime.utcnow().isoformat(),
        "status": "processed",
    }


def generate_mock_chat_data(chat_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate mock chat data"""
    return {
        "chat_id": chat_id or "chat-123-456",
        "user_id": "user-123-456-789",
        "title": "Test Chat",
        "created_at": datetime.utcnow().isoformat(),
    }


def generate_mock_message_data(
    message_id: Optional[str] = None, role: str = "user"
) -> Dict[str, Any]:
    """Generate mock message data"""
    return {
        "id": message_id or "msg-123-456",
        "chat_id": "chat-123-456",
        "user_id": "user-123-456-789",
        "role": role,
        "content": "Test message content",
        "created_at": datetime.utcnow().isoformat(),
    }
