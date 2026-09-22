from __future__ import annotations

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from common.pagination import Page, PageParams


class Item(BaseModel):
    id: int


def build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/items", response_model=Page[Item])
    async def _items(params: PageParams = Depends()) -> Page[Item]:
        return Page.build([Item(id=1)], total=137, params=params)

    return app


def test_offset_va_limit():
    params = PageParams(page=3, size=20)
    assert params.offset == 40
    assert params.limit == 20


def test_trang_dau_offset_bang_0():
    assert PageParams(page=1, size=50).offset == 0


async def test_mac_dinh(make_client):
    async with make_client(build_app()) as client:
        resp = await client.get("/items")
    assert resp.json() == {"items": [{"id": 1}], "total": 137, "page": 1, "size": 20}


async def test_size_vuot_gioi_han_ra_422(make_client):
    async with make_client(build_app()) as client:
        resp = await client.get("/items", params={"size": 101})
    assert resp.status_code == 422
    assert resp.json()["code"] == "validation_error"


async def test_page_0_ra_422(make_client):
    async with make_client(build_app()) as client:
        resp = await client.get("/items", params={"page": 0})
    assert resp.status_code == 422
