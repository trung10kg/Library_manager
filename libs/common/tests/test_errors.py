"""Moi loai loi phai ra cung dinh dang {detail, code}."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from common.errors import AppError


class Body(BaseModel):
    title: str = Field(min_length=3)


def build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/app-error")
    async def _app_error() -> None:
        raise AppError(409, "copy_not_available", "Ban sao khong con san")

    @app.get("/http-error")
    async def _http_error() -> None:
        raise HTTPException(status_code=404, detail="Khong thay sach")

    @app.get("/boom")
    async def _boom() -> None:
        raise RuntimeError("bug trong service")

    @app.post("/validate")
    async def _validate(body: Body) -> dict[str, str]:
        return {"title": body.title}

    return app


async def test_app_error(make_client):
    async with make_client(build_app()) as client:
        resp = await client.get("/app-error")
    assert resp.status_code == 409
    assert resp.json() == {"detail": "Ban sao khong con san", "code": "copy_not_available"}


async def test_http_exception_thanh_cung_dinh_dang(make_client):
    async with make_client(build_app()) as client:
        resp = await client.get("/http-error")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Khong thay sach", "code": "not_found"}


async def test_route_khong_ton_tai(make_client):
    """Detail mac dinh cua Starlette la "Not Found" - phai doi sang tieng Viet."""
    async with make_client(build_app()) as client:
        resp = await client.get("/khong-co-dau")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Khong tim thay duong dan", "code": "not_found"}


async def test_phuong_thuc_sai(make_client):
    async with make_client(build_app()) as client:
        resp = await client.post("/app-error")
    assert resp.status_code == 405
    assert resp.json()["code"] == "method_not_allowed"
    assert resp.json()["detail"] == "Phuong thuc khong duoc ho tro"


async def test_loi_khong_luong_truoc_khong_lo_chi_tiet(make_client):
    async with make_client(build_app()) as client:
        resp = await client.get("/boom")
    assert resp.status_code == 500
    body = resp.json()
    assert body == {"detail": "Loi he thong", "code": "internal_error"}
    assert "bug trong service" not in resp.text


async def test_validation_co_ten_field(make_client):
    async with make_client(build_app()) as client:
        resp = await client.post("/validate", json={"title": "ab"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "validation_error"
    assert body["errors"][0]["field"] == "title"
