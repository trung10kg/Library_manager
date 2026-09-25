"""Goi service khac qua HTTP.

Dung MOT httpx.AsyncClient cho ca vong doi service, tao trong lifespan.
Luon forward header Authorization de service kia tu kiem quyen.

Luu y kien truc: 5 service dung chung mot database, nen ve ky thuat co the
query thang bang cua nhau. Khong lam the. Doc du lieu ngoai pham vi so huu
thi di qua day.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from common.errors import AppError
from common.security import CurrentUser

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5.0


def create_http_client(timeout: float = DEFAULT_TIMEOUT) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout)


class ServiceClient:
    """Wrapper quanh mot service dich."""

    def __init__(self, base_url: str, client: httpx.AsyncClient, name: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client
        self.name = name

    async def get(self, path: str, *, user: CurrentUser | None = None, **kw: Any) -> Any:
        return await self._request("GET", path, user=user, **kw)

    async def post(self, path: str, *, user: CurrentUser | None = None, **kw: Any) -> Any:
        return await self._request("POST", path, user=user, **kw)

    async def patch(self, path: str, *, user: CurrentUser | None = None, **kw: Any) -> Any:
        return await self._request("PATCH", path, user=user, **kw)

    async def delete(self, path: str, *, user: CurrentUser | None = None, **kw: Any) -> Any:
        return await self._request("DELETE", path, user=user, **kw)

    async def _request(
        self, method: str, path: str, *, user: CurrentUser | None = None, **kw: Any
    ) -> Any:
        headers = dict(kw.pop("headers", {}) or {})
        if user is not None:
            headers["Authorization"] = f"Bearer {user.token}"

        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = await self.client.request(method, url, headers=headers, **kw)
        except httpx.TimeoutException:
            logger.warning("Timeout khi goi %s %s", self.name, url)
            raise AppError(503, "upstream_unavailable", f"{self.name} khong phan hoi") from None
        except httpx.RequestError as exc:
            logger.warning("Loi mang khi goi %s %s: %s", self.name, url, exc)
            raise AppError(503, "upstream_unavailable", f"Khong goi duoc {self.name}") from None

        if resp.status_code >= 500:
            logger.warning("%s tra %s cho %s", self.name, resp.status_code, url)
            raise AppError(503, "upstream_unavailable", f"{self.name} dang loi")

        if resp.status_code >= 400:
            # Giu nguyen code nghiep vu cua service kia de client thay dung loi.
            body = self._safe_json(resp)
            raise AppError(
                resp.status_code,
                str(body.get("code") or "upstream_error"),
                str(body.get("detail") or f"{self.name} tu choi yeu cau"),
            )

        if resp.status_code == 204 or not resp.content:
            return None
        return self._safe_json(resp)

    @staticmethod
    def _safe_json(resp: httpx.Response) -> dict[str, Any]:
        try:
            data = resp.json()
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {"data": data}
