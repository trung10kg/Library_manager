"""Goi service khac: forward token, va doi loi upstream sang AppError."""

from __future__ import annotations

import httpx
import pytest
import respx

from common.errors import AppError
from common.http import ServiceClient, create_http_client
from common.security import CurrentUser, Role

BASE = "http://catalog-service:8000"


@pytest.fixture
def user() -> CurrentUser:
    return CurrentUser(
        id=2,
        username="thuthu01",
        roles=frozenset({Role.LIBRARIAN}),
        reader_id=None,
        token="TOKEN123",
    )


@pytest.fixture
async def service():
    async with create_http_client() as client:
        yield ServiceClient(BASE, client, "catalog-service")


async def test_forward_authorization(service, user):
    with respx.mock(base_url=BASE) as mock:
        route = mock.get("/copies/1").mock(return_value=httpx.Response(200, json={"id": 1}))
        data = await service.get("/copies/1", user=user)

    assert data == {"id": 1}
    assert route.calls.last.request.headers["Authorization"] == "Bearer TOKEN123"


async def test_khong_co_user_thi_khong_gan_header(service):
    with respx.mock(base_url=BASE) as mock:
        route = mock.get("/health").mock(return_value=httpx.Response(200, json={"status": "ok"}))
        await service.get("/health")

    assert "Authorization" not in route.calls.last.request.headers


async def test_204_tra_none(service, user):
    with respx.mock(base_url=BASE) as mock:
        mock.post("/copies/1/release").mock(return_value=httpx.Response(204))
        assert await service.post("/copies/1/release", user=user) is None


async def test_loi_5xx_thanh_503(service, user):
    with respx.mock(base_url=BASE) as mock:
        mock.get("/copies/1").mock(return_value=httpx.Response(500, text="boom"))
        with pytest.raises(AppError) as exc:
            await service.get("/copies/1", user=user)

    assert exc.value.status_code == 503
    assert exc.value.code == "upstream_unavailable"


async def test_timeout_thanh_503(service, user):
    with respx.mock(base_url=BASE) as mock:
        mock.get("/copies/1").mock(side_effect=httpx.TimeoutException("qua lau"))
        with pytest.raises(AppError) as exc:
            await service.get("/copies/1", user=user)

    assert exc.value.status_code == 503
    assert exc.value.code == "upstream_unavailable"


async def test_loi_mang_thanh_503(service, user):
    with respx.mock(base_url=BASE) as mock:
        mock.get("/copies/1").mock(side_effect=httpx.ConnectError("khong noi duoc"))
        with pytest.raises(AppError) as exc:
            await service.get("/copies/1", user=user)

    assert exc.value.status_code == 503


async def test_4xx_giu_nguyen_code_cua_service_kia(service, user):
    with respx.mock(base_url=BASE) as mock:
        mock.post("/copies/1/checkout").mock(
            return_value=httpx.Response(
                409, json={"detail": "Ban sao khong con san", "code": "copy_not_available"}
            )
        )
        with pytest.raises(AppError) as exc:
            await service.post("/copies/1/checkout", user=user)

    assert exc.value.status_code == 409
    assert exc.value.code == "copy_not_available"
    assert exc.value.detail == "Ban sao khong con san"


async def test_4xx_body_khong_phai_json(service, user):
    with respx.mock(base_url=BASE) as mock:
        mock.get("/copies/1").mock(return_value=httpx.Response(404, text="<html>404</html>"))
        with pytest.raises(AppError) as exc:
            await service.get("/copies/1", user=user)

    assert exc.value.status_code == 404
    assert exc.value.code == "upstream_error"
