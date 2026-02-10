"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_login_success(client, admin_user):
    """Test successful login with valid credentials."""
    response = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpass123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    """Test login with wrong password returns 401."""
    response = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Test login with non-existent user returns 401."""
    response = await client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "password"}
    )

    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_login_missing_fields(client):
    """Test login with missing fields returns 422."""
    # Missing password
    response = await client.post(
        "/auth/login",
        json={"email": "test@example.com"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    """Test accessing protected endpoint without token returns 401."""
    response = await client.get("/employees")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(client):
    """Test accessing protected endpoint with invalid token returns 401."""
    response = await client.get(
        "/employees",
        headers={"Authorization": "Bearer invalid_token_here"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(client, auth_headers):
    """Test accessing protected endpoint with valid token succeeds."""
    response = await client.get(
        "/employees",
        headers=auth_headers
    )

    assert response.status_code == 200
