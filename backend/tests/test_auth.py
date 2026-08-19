"""
test_auth.py
"""

import pytest


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alice"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate(client, test_user):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "password123"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login(client, test_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "wrongpass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client, auth_headers):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"
