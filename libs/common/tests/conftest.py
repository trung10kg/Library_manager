from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from common.errors import register_error_handlers
from common.testing import generate_rsa_keypair


@pytest.fixture(scope="session")
def keypair() -> tuple[str, str]:
    return generate_rsa_keypair()


@pytest.fixture(scope="session")
def private_key(keypair: tuple[str, str]) -> str:
    return keypair[0]


@pytest.fixture(scope="session")
def public_key(keypair: tuple[str, str]) -> str:
    return keypair[1]


@pytest.fixture
def make_client():
    """Tra ve ham dung AsyncClient cho mot FastAPI app da gan error handler.

    raise_app_exceptions=False de handler Exception duoc chay that va tra
    response 500, thay vi httpx nem nguoc exception ra test.
    """

    def _make(app: FastAPI) -> AsyncClient:
        register_error_handlers(app)
        return AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        )

    return _make
