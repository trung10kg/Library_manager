from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.deps import AnyUser, FineServiceDep
from app.schemas.fine import OutstandingOut

router = APIRouter(prefix="/readers", tags=["fines"])


@router.get(
    "/{reader_id}/outstanding",
    response_model=OutstandingOut,
    summary="Cong no phat cua ban doc - circulation goi truoc khi cho muon",
)
async def reader_outstanding(
    reader_id: int, user: AnyUser, service: FineServiceDep
) -> OutstandingOut:
    return await service.outstanding(user, reader_id)
