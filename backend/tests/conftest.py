"""
conftest.py

pytest 共享 fixture。
"""

import os
import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise

# 每个 pytest 进程使用独立的 SQLite 文件，避免 Windows 文件锁冲突
_db_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="bai_zhan_test_")
os.close(_db_fd)
TEST_DB_PATH = Path(_db_path)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["LLM_MOCK"] = "true"

from app.config import TORTOISE_ORM  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()
    try:
        TEST_DB_PATH.unlink(missing_ok=True)
    except PermissionError:
        pass


@pytest.fixture
async def client(init_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def test_user(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "testpass123"},
    )
    return resp.json()


@pytest.fixture
async def auth_headers(client, test_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
