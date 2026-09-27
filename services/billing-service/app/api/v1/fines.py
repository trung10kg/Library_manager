from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import AdminUser, AnyUser, FineServiceDep, StaffUser
from app.models.fine import FineStatus, FineType
from app.schemas.fine import FineCreate, FineDetailOut, FineOut, PaymentCreate, WaiveIn
from common.pagination import Page, PageParams

router = APIRouter(prefix="/fines", tags=["fines"])


@router.get(
    "",
    response_model=Page[FineOut],
    summary="Danh sach khoan phat (READER chi thay cua minh)",
)
async def list_fines(
    user: AnyUser,
    service: FineServiceDep,
    params: Annotated[PageParams, Depends()],
    reader_id: Annotated[int | None, Query(gt=0)] = None,
    status_: Annotated[FineStatus | None, Query(alias="status")] = None,
    fine_type: FineType | None = None,
) -> Page[FineOut]:
    return await service.list(
        user, params, reader_id=reader_id, status=status_, fine_type=fine_type
    )


@router.get(
    "/{fine_id}",
    response_model=FineDetailOut,
    summary="Chi tiet khoan phat kem lich su nop tien",
)
async def get_fine(fine_id: int, user: AnyUser, service: FineServiceDep) -> FineDetailOut:
    return await service.get(user, fine_id)


@router.post(
    "",
    response_model=FineDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Lap khoan phat thu cong (thu thu / admin)",
)
async def create_fine(body: FineCreate, user: StaffUser, service: FineServiceDep) -> FineDetailOut:
    return await service.create(user, body)


@router.post(
    "/{fine_id}/payments",
    response_model=FineDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ghi nhan nop tien - tra nhieu lan duoc, du thi tu chuyen PAID (thu thu / admin)",
)
async def pay_fine(
    fine_id: int, body: PaymentCreate, user: StaffUser, service: FineServiceDep
) -> FineDetailOut:
    return await service.pay(user, fine_id, body)


@router.post(
    "/{fine_id}/waive",
    response_model=FineDetailOut,
    summary="Mien phan con no cua khoan phat (ADMIN)",
)
async def waive_fine(
    fine_id: int, body: WaiveIn, admin: AdminUser, service: FineServiceDep
) -> FineDetailOut:
    return await service.waive(admin, fine_id, body)
