from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import PaymentServiceDep, StaffUser
from app.models.payment import PaymentMethod
from app.schemas.fine import PaymentFilter, PaymentPage
from common.pagination import PageParams

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get(
    "",
    response_model=PaymentPage,
    summary="Doi soat tien thu theo khoang ngay (thu thu / admin)",
)
async def list_payments(
    user: StaffUser,
    service: PaymentServiceDep,
    params: Annotated[PageParams, Depends()],
    from_date: Annotated[date | None, Query(description="Tu ngay (UTC), bao gom")] = None,
    to_date: Annotated[date | None, Query(description="Den ngay (UTC), bao gom")] = None,
    method: PaymentMethod | None = None,
    staff_id: Annotated[int | None, Query(gt=0)] = None,
    reader_id: Annotated[int | None, Query(gt=0)] = None,
) -> PaymentPage:
    filters = PaymentFilter(
        from_date=from_date,
        to_date=to_date,
        method=method,
        staff_id=staff_id,
        reader_id=reader_id,
    )
    return await service.list(params, filters)
