from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

from common.testing import generate_rsa_keypair

_PRIVATE_KEY, _PUBLIC_KEY = generate_rsa_keypair()

# Phai dat TRUOC khi import app.core.config: Settings doc env ngay luc khoi tao.
os.environ["JWT_PUBLIC_KEY"] = _PUBLIC_KEY
os.environ.pop("JWT_PUBLIC_KEY_PATH", None)
os.environ.setdefault(
    "DATABASE_URL",
    "mysql+aiomysql://root:1234@127.0.0.1:3306/library_test_db?charset=utf8mb4",
)

from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def private_key() -> str:
    return _PRIVATE_KEY


@pytest.fixture
async def client():
    """Client khong chay lifespan - test Phase 1 chua cham database."""
    transport = ASGITransport(app=create_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
