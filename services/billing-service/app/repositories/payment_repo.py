from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment

_PAYMENT_COLUMNS = (
    "payments.id, payments.fine_id, payments.amount, payments.paid_at, payments.method, "
    "payments.staff_id, payments.notes"
)

_PAID_TOTAL = text("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE fine_id = :fine_id")


class PaymentRepository:
    """Truy van bang payments. Khong chua nghiep vu, khong raise HTTP."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, payment: Payment) -> None:
        self.session.add(payment)

    async def paid_total(self, fine_id: int) -> Decimal:
        return Decimal(await self.session.scalar(_PAID_TOTAL, {"fine_id": fine_id}) or 0)

    async def search(
        self,
        *,
        paid_from: datetime | None,
        paid_before: datetime | None,
        method: str | None,
        staff_id: int | None,
        reader_id: int | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Payment], int, Decimal]:
        """(trang ket qua, tong so dong, tong tien cua moi dong khop).

        paid_from bao gom, paid_before khong bao gom - [paid_from, paid_before).
        """
        conditions: list[str] = []
        params: dict[str, object] = {}
        if paid_from is not None:
            conditions.append("payments.paid_at >= :paid_from")
            params["paid_from"] = paid_from
        if paid_before is not None:
            conditions.append("payments.paid_at < :paid_before")
            params["paid_before"] = paid_before
        if method:
            conditions.append("payments.method = :method")
            params["method"] = method
        if staff_id is not None:
            conditions.append("payments.staff_id = :staff_id")
            params["staff_id"] = staff_id
        if reader_id is not None:
            conditions.append("fines.reader_id = :reader_id")
            params["reader_id"] = reader_id
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        source = "payments JOIN fines ON fines.id = payments.fine_id"

        summary = (
            await self.session.execute(
                text(f"SELECT COUNT(*), COALESCE(SUM(payments.amount), 0) FROM {source} {where}"),
                params,
            )
        ).one()

        page_sql = text(
            f"SELECT {_PAYMENT_COLUMNS} FROM {source} {where} "
            "ORDER BY payments.paid_at DESC, payments.id DESC LIMIT :limit OFFSET :offset"
        )
        result = await self.session.execute(
            select(Payment).from_statement(page_sql),
            {**params, "limit": limit, "offset": offset},
        )
        return list(result.scalars()), int(summary[0]), Decimal(summary[1])
