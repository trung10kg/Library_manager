"""Xac thuc JWT RS256 - dung chung cho ca 5 service.

auth-service la noi duy nhat giu private key va ky token. Cac service khac
chi co public key va tu verify, khong goi nguoc lai auth-service.

Khac SKILL.md mot diem: schema dung bang noi `user_roles` (nhieu-nhieu) nen
mot user co the co nhieu role. Claim vi vay la `roles` dang mang, va
CurrentUser.roles la frozenset thay vi mot role don.

ID la BIGINT trong schema, nen la `int` - khong phai UUID.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict, ValidationError

from common.errors import AppError

ISSUER = "library-auth"
ALGORITHM = "RS256"

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# Duong dan login di qua gateway. Swagger (ca /docs gop o gateway) dung no de
# hien o username/mat khau trong nut Authorize - dang nhap mot lan la thu duoc
# API cua moi service.
TOKEN_URL = "/api/auth/login"


class Role(StrEnum):
    ADMIN = "ADMIN"
    LIBRARIAN = "LIBRARIAN"
    READER = "READER"


class CurrentUser(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    username: str
    roles: frozenset[Role]
    reader_id: int | None = None
    # Giu lai token tho de forward khi goi service khac.
    token: str

    def has_any(self, *roles: Role) -> bool:
        return bool(self.roles.intersection(roles))

    @property
    def is_staff(self) -> bool:
        return self.has_any(Role.ADMIN, Role.LIBRARIAN)


# Van doc header "Authorization: Bearer <token>" nhu HTTPBearer; khac o cho
# OpenAPI khai bao luong password de Swagger co form dang nhap.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL, auto_error=False)


def decode_token(
    token: str,
    public_key: str,
    expected_type: str = TOKEN_TYPE_ACCESS,
    *,
    verify_exp: bool = True,
) -> dict[str, Any]:
    """Giai ma va kiem tra token. Moi that bai deu thanh 401.

    verify_exp=False chi dung cho logout: token het han van thu hoi duoc.
    """
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            options={"require": ["exp", "iat", "sub", "jti"], "verify_exp": verify_exp},
        )
    except jwt.ExpiredSignatureError:
        raise AppError(401, "token_expired", "Token da het han") from None
    except jwt.InvalidTokenError:
        raise AppError(401, "invalid_token", "Token khong hop le") from None

    if payload.get("type") != expected_type:
        raise AppError(401, "invalid_token", "Sai loai token")
    return payload


def build_get_current_user(
    public_key: str,
) -> Callable[..., Awaitable[CurrentUser]]:
    """Tao dependency get_current_user. Moi service goi mot lan trong deps.py."""

    async def get_current_user(
        token: str | None = Depends(oauth2_scheme),
    ) -> CurrentUser:
        if not token:
            raise AppError(401, "not_authenticated", "Thieu access token")

        payload = decode_token(token, public_key)
        try:
            return CurrentUser(
                id=int(payload["sub"]),
                username=payload["username"],
                roles=frozenset(payload.get("roles") or []),
                reader_id=payload.get("reader_id"),
                token=token,
            )
        except (KeyError, ValueError, TypeError, ValidationError):
            # Claim thieu hoac role la: van la token hong -> 401, khong phai 500.
            raise AppError(401, "invalid_token", "Token thieu thong tin bat buoc") from None

    return get_current_user


def make_require_roles(
    get_current_user: Callable[..., Awaitable[CurrentUser]],
) -> Callable[..., Callable[..., Awaitable[CurrentUser]]]:
    """Tao ham require_roles gan voi get_current_user cua service."""

    def require_roles(*roles: Role) -> Callable[..., Awaitable[CurrentUser]]:
        async def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
            if not user.has_any(*roles):
                raise AppError(403, "forbidden", "Khong du quyen")
            return user

        return checker

    return require_roles
