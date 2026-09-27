from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from sqlalchemy import bindparam, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fine import Fine

_FINE_COLUMNS = (
    "fines.id, fines.loan_item_id, fines.reader_id, fines.fine_type, fines.amount, "
    "fines.status, fines.issued_at, fines.notes"
)

_GET = text(f"SELECT {_FINE_COLUMNS} FROM fines WHERE fines.id = :fine_id")

# Khoa dong fine toi het transaction: moi thao tac doi tien (nop, mien) deu di
# qua day, nen hai thu thu thao tac cung luc tren mot khoan se chay noi tiep.
_GET_FOR_UPDATE = text(f"SELECT {_FINE_COLUMNS} FROM fines WHERE fines.id = :fine_id FOR UPDATE")

_PAID_TOTALS = text(
    "SELECT fine_id, SUM(amount) FROM payments WHERE fine_id IN :fine_ids GROUP BY fine_id"
).bindparams(bindparam("fine_ids", expanding=True))

# Chi khoan UNPAID con no. Subquery tuong quan dung idx_payments_fine thay vi
# gom nhom ca bang payments.
_OUTSTANDING = text(
    "SELECT COUNT(*), "
    "COALESCE(SUM(fines.amount - COALESCE("
    "(SELECT SUM(p.amount) FROM payments p WHERE p.fine_id = fines.id), 0)), 0) "
    "FROM fines WHERE fines.reader_id = :reader_id AND fines.status = 'UNPAID'"
)


class FineRepository:
    """Truy van bang fines. Khong chua nghiep vu, khong raise HTTP."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, fine: Fine) -> None:
        self.session.add(fine)

    async def get(
        self, fine_id: int, *, with_payments: bool = False, for_update: bool = False
    ) -> Fine | None:
        stmt = select(Fine).from_statement(_GET_FOR_UPDATE if for_update else _GET)
        if with_payments:
            # populate_existing: object co the da nam trong session (vua nop
            # tien xong) - nap lai de payments khong cu.
            stmt = stmt.options(selectinload(Fine.payments)).execution_options(
                populate_existing=True
            )
        result = await self.session.execute(stmt, {"fine_id": fine_id})
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        reader_id: int | None,
        status: str | None,
        fine_type: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Fine], int]:
        # Chi ghep cac doan WHERE viet san; gia tri luon di qua tham so :ten.
        conditions: list[str] = []
        params: dict[str, object] = {}
        if reader_id is not None:
            conditions.append("fines.reader_id = :reader_id")
            params["reader_id"] = reader_id
        if status:
            conditions.append("fines.status = :status")
            params["status"] = status
        if fine_type:
            conditions.append("fines.fine_type = :fine_type")
            params["fine_type"] = fine_type
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        total = await self.session.scalar(text(f"SELECT COUNT(*) FROM fines {where}"), params)

        page_sql = text(
            f"SELECT {_FINE_COLUMNS} FROM fines {where} "
            "ORDER BY fines.issued_at DESC, fines.id DESC LIMIT :limit OFFSET :offset"
        )
        result = await self.session.execute(
            select(Fine).from_statement(page_sql), {**params, "limit": limit, "offset": offset}
        )
        return list(result.scalars()), int(total or 0)

    async def paid_totals(self, fine_ids: Iterable[int]) -> dict[int, Decimal]:
        """fine_id -> tong da nop. Khoan chua nop dong nao khong co trong dict."""
        ids = list(fine_ids)
        if not ids:
            return {}
        result = await self.session.execute(_PAID_TOTALS, {"fine_ids": ids})
        return {int(fine_id): total for fine_id, total in result.all()}

    async def outstanding(self, reader_id: int) -> tuple[int, Decimal]:
        """(so khoan UNPAID, tong con no) cua mot ban doc."""
        row = (await self.session.execute(_OUTSTANDING, {"reader_id": reader_id})).one()
        return int(row[0]), Decimal(row[1])
