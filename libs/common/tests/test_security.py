"""Xac thuc JWT: token hong duoi moi dang deu phai ra 401, khong phai 500."""

from __future__ import annotations

import uuid
from datetime import timedelta

import jwt
import pytest
from fastapi import Depends, FastAPI

from common.datetime_utils import utc_now
from common.security import (
    ALGORITHM,
    ISSUER,
    TOKEN_TYPE_REFRESH,
    CurrentUser,
    Role,
    build_get_current_user,
    make_require_roles,
)
from common.testing import make_token


def build_app(public_key: str) -> FastAPI:
    get_current_user = build_get_current_user(public_key)
    require_roles = make_require_roles(get_current_user)

    app = FastAPI()

    @app.get("/me")
    async def _me(user: CurrentUser = Depends(get_current_user)) -> dict:
        return {"id": user.id, "roles": sorted(user.roles), "reader_id": user.reader_id}

    @app.get("/staff")
    async def _staff(
        user: CurrentUser = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)),
    ) -> dict:
        return {"username": user.username}

    return app


def raw_token(private_key: str, **overrides) -> str:
    """Token voi payload tu che, de test claim hong."""
    now = utc_now()
    payload = {
        "sub": "1",
        "username": "tester",
        "roles": ["LIBRARIAN"],
        "reader_id": None,
        "type": "access",
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "iss": ISSUER,
    }
    payload.update(overrides)
    for key in [k for k, v in payload.items() if v is ...]:
        del payload[key]
    return jwt.encode(payload, private_key, algorithm=ALGORITHM)


@pytest.fixture
def client(make_client, public_key):
    return make_client(build_app(public_key))


async def test_token_hop_le(client, private_key):
    token = make_token(private_key, user_id=7, roles=[Role.READER], reader_id=42)
    async with client as c:
        resp = await c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == {"id": 7, "roles": ["READER"], "reader_id": 42}


async def test_nhieu_role(client, private_key):
    token = make_token(private_key, roles=[Role.ADMIN, Role.READER])
    async with client as c:
        resp = await c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["roles"] == ["ADMIN", "READER"]


async def test_thieu_token(client):
    async with client as c:
        resp = await c.get("/me")
    assert resp.status_code == 401
    assert resp.json()["code"] == "not_authenticated"


async def test_token_het_han(client, private_key):
    token = make_token(private_key, ttl=timedelta(minutes=-1))
    async with client as c:
        resp = await c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "token_expired"


async def test_ky_bang_key_khac(client):
    from common.testing import generate_rsa_keypair

    other_private, _ = generate_rsa_keypair()
    token = make_token(other_private)
    async with client as c:
        resp = await c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_token"


async def test_refresh_token_khong_dung_duoc_thay_access(client, private_key):
    token = make_token(private_key, token_type=TOKEN_TYPE_REFRESH)
    async with client as c:
        resp = await c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_token"


async def test_sai_issuer(client, private_key):
    token = make_token(private_key, issuer="ke-gia-mao")
    async with client as c:
        resp = await c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_token"


async def test_thieu_claim_bat_buoc_ra_401_chu_khong_500(client, private_key):
    token = raw_token(private_key, username=...)
    async with client as c:
        resp = await c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_token"


async def test_role_la_ra_401_chu_khong_500(client, private_key):
    token = raw_token(private_key, roles=["SIEU_NHAN"])
    async with client as c:
        resp = await c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_token"


async def test_thieu_jti(client, private_key):
    token = raw_token(private_key, jti=...)
    async with client as c:
        resp = await c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


async def test_du_quyen(client, private_key):
    token = make_token(private_key, username="thuthu01", roles=[Role.LIBRARIAN])
    async with client as c:
        resp = await c.get("/staff", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == {"username": "thuthu01"}


async def test_thieu_quyen_ra_403(client, private_key):
    token = make_token(private_key, roles=[Role.READER])
    async with client as c:
        resp = await c.get("/staff", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"


async def test_thieu_token_o_route_can_quyen_ra_401_khong_phai_403(client):
    async with client as c:
        resp = await c.get("/staff")
    assert resp.status_code == 401
