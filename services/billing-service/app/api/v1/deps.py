"""Dependency dung trong router cua billing-service."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.fine_service import FineService
from app.services.payment_service import PaymentService
from common.db import get_session
from common.security import CurrentUser, Role, build_get_current_user, make_require_roles

get_current_user = build_get_current_user(settings.jwt_public_key)
require_roles = make_require_roles(get_current_user)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AnyUser = Annotated[CurrentUser, Depends(get_current_user)]
StaffUser = Annotated[CurrentUser, Depends(require_roles(Role.ADMIN, Role.LIBRARIAN))]
AdminUser = Annotated[CurrentUser, Depends(require_roles(Role.ADMIN))]


def get_fine_service(session: SessionDep) -> FineService:
    return FineService(session)


def get_payment_service(session: SessionDep) -> PaymentService:
    return PaymentService(session)


FineServiceDep = Annotated[FineService, Depends(get_fine_service)]
PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
