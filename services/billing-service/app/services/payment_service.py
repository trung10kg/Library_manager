from __future__ import annotations

from datetime import datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.payment_repo import PaymentRepository
from app.schemas.fine import PaymentFilter, PaymentOut, PaymentPage
from common.errors import AppError
from common.pagination import PageParams


class PaymentService:
    """Doi soat tien thu. Chi thu thu / admin goi toi (chan o router)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.payments = PaymentRepository(session)

    async def list(self, params: PageParams, filters: PaymentFilter) -> PaymentPage:
        if filters.from_date and filters.to_date and filters.from_date > filters.to_date:
            raise AppError(422, "invalid_date_range", "from_date phai truoc hoac bang to_date")

        # Ngay tinh theo UTC, khop paid_at luu UTC. to_date bao gom ca ngay do.
        paid_from = datetime.combine(filters.from_date, time.min) if filters.from_date else None
        paid_before = (
            datetime.combine(filters.to_date + timedelta(days=1), time.min)
            if filters.to_date
            else None
        )
        payments, total, total_amount = await self.payments.search(
            paid_from=paid_from,
            paid_before=paid_before,
            method=filters.method,
            staff_id=filters.staff_id,
            reader_id=filters.reader_id,
            offset=params.offset,
            limit=params.limit,
        )
        return PaymentPage(
            items=[PaymentOut.model_validate(p) for p in payments],
            total=total,
            page=params.page,
            size=params.size,
            total_amount=total_amount,
        )
