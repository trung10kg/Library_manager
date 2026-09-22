"""Khung service: health va dinh dang loi."""

from __future__ import annotations

from app.main import API_PREFIX

SERVICE_NAME = "reader-service"


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": SERVICE_NAME}


async def test_health_duoi_prefix_goi_duoc_qua_gateway(client):
    resp = await client.get(f"{API_PREFIX}/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == SERVICE_NAME


async def test_openapi_nam_duoi_prefix(client):
    assert (await client.get(f"{API_PREFIX}/openapi.json")).status_code == 200
    # Duong mac dinh cua FastAPI phai khong con, neu khong gateway se khong
    # dinh tuyen duoc toi docs.
    assert (await client.get("/openapi.json")).status_code == 404


async def test_route_la_tra_json_dung_dinh_dang(client):
    resp = await client.get(f"{API_PREFIX}/khong-co-dau")
    assert resp.status_code == 404
    assert resp.json()["code"] == "not_found"
