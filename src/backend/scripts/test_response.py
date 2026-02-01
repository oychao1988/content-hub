"""Test script to see response format"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import pytest
from fastapi.testclient import TestClient
from tests.conftest import client, test_db

def test_get_response_format(client: TestClient):
    """Test to see what the error response looks like"""
    # Register first user
    user_data1 = {
        "email": "test@example.com",
        "username": "testuser1",
        "password": "password123"
    }
    response1 = client.post("/api/v1/auth/register", json=user_data1)
    print("First register response:", response1.status_code, response1.json())

    # Try to register duplicate user
    user_data2 = {
        "email": "test@example.com",
        "username": "testuser2",
        "password": "password123"
    }
    response2 = client.post("/api/v1/auth/register", json=user_data2)
    print("\nSecond register response (should fail):", response2.status_code, response2.json())

    assert response2.status_code == 400

# Run the test manually
if __name__ == "__main__":
    from tests.conftest import client, test_db
    import pytest

    pytest.main([__file__, "-v"])
