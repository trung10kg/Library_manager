"""Endpoint /health dung chung."""

from __future__ import annotations

from fastapi import FastAPI


def add_health_routes(app: FastAPI, prefix: str, service_name: str) -> None:
    """Gan /health o hai cho.

    - `/health` cho healthcheck cua Docker (goi thang vao container).
    - `<prefix>/health` de goi duoc qua gateway ma gateway khong can rule
      rieng cat prefix.
    """

    async def health() -> dict[str, str]:
        return {"status": "ok", "service": service_name}

    # Ban goc chi de Docker goi, gateway khong dinh tuyen toi -> an khoi docs.
    app.add_api_route("/health", health, methods=["GET"], include_in_schema=False)
    app.add_api_route(f"{prefix}/health", health, methods=["GET"], tags=["health"])
