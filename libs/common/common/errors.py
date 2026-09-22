"""Loi va dinh dang response loi dung chung.

Moi loi tra ve deu co dang:

    {"detail": "<thong diep tieng Viet>", "code": "<snake_case>"}

Rieng loi 422 co them khoa "errors" liet ke tung field sai - khong co no thi
client khong biet field nao hong.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# Map status code -> code mac dinh, dung cho HTTPException do FastAPI tu sinh
# (vd 404 khi khong khop route nao).
_DEFAULT_CODES: dict[int, str] = {
    400: "bad_request",
    401: "not_authenticated",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "too_many_requests",
    503: "service_unavailable",
}

# FastAPI/Starlette sinh detail tieng Anh ("Not Found", "Method Not Allowed").
# Doi sang tieng Viet de toan bo API noi mot thu tieng.
_DEFAULT_MESSAGES: dict[int, str] = {
    400: "Yeu cau khong hop le",
    401: "Chua dang nhap",
    403: "Khong du quyen",
    404: "Khong tim thay duong dan",
    405: "Phuong thuc khong duoc ho tro",
    409: "Xung dot du lieu",
    422: "Du lieu gui len khong hop le",
    429: "Qua nhieu yeu cau",
    503: "Dich vu tam thoi khong san sang",
}


class AppError(Exception):
    """Loi nghiep vu co chu dich. Router/service raise cai nay, khong raise
    HTTPException truc tiep."""

    def __init__(self, status_code: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail

    def __repr__(self) -> str:
        return f"AppError({self.status_code}, {self.code!r}, {self.detail!r})"


def _standard_phrase(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return ""


def error_response(status_code: int, code: str, detail: str, **extra: Any) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail, "code": code, **extra})


def register_error_handlers(app: FastAPI) -> None:
    """Dang ky day du 4 handler. Goi trong create_app() cua moi service."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                # Bo phan tu dau ("body"/"query"/"path") cho gon.
                "field": ".".join(str(part) for part in err["loc"][1:]) or str(err["loc"][0]),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        return error_response(
            422, "validation_error", "Du lieu gui len khong hop le", errors=errors
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _DEFAULT_CODES.get(exc.status_code, "http_error")
        detail = exc.detail if isinstance(exc.detail, str) else ""
        # Chi thay khi detail van la cau mac dinh cua Starlette; thong diep
        # do nguoi viet code dat thi giu nguyen.
        if not detail or detail == _standard_phrase(exc.status_code):
            detail = _DEFAULT_MESSAGES.get(exc.status_code, "Yeu cau that bai")
        return error_response(exc.status_code, code, detail)

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Log kem traceback nhung KHONG tra chi tiet ra ngoai.
        logger.exception("Loi khong luong truoc tai %s %s", request.method, request.url.path)
        return error_response(500, "internal_error", "Loi he thong")
