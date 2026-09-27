from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fine import Fine, FineStatus
from app.models.payment import Payment
from app.repositories.fine_repo import FineRepository
from app.repositories.payment_repo import PaymentRepository
from app.schemas.fine import (
    ZERO,
    FineCreate,
    FineDetailOut,
    FineOut,
    OutstandingOut,
    PaymentCreate,
    WaiveIn,
)
from common.errors import AppError
from common.pagination import Page, PageParams
from common.security import CurrentUser

NOTES_MAX = 300
WAIVE_PREFIX = "[Mien phat]"


class FineService:
    """Khoan phat: xem, lap, nop tien, mien.

    READER chi thay khoan phat cua chinh minh - kiem o day, khong dua vao viec
    client khong gui reader_id nguoi khac.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.fines = FineRepository(session)
        self.payments = PaymentRepository(session)

    # --- Xem ---------------------------------------------------------------

    async def list(
        self,
        user: CurrentUser,
        params: PageParams,
        *,
        reader_id: int | None,
        status: FineStatus | None,
        fine_type: str | None,
    ) -> Page[FineOut]:
        if not user.is_staff:
            if reader_id is not None and reader_id != user.reader_id:
                raise AppError(403, "forbidden", "Chi xem duoc khoan phat cua chinh minh")
            if user.reader_id is None:
                # Tai khoan READER chua gan ho so ban doc: khong co khoan nao.
                return Page.build([], 0, params)
            reader_id = user.reader_id

        fines, total = await self.fines.search(
            reader_id=reader_id,
            status=status,
            fine_type=fine_type,
            offset=params.offset,
            limit=params.limit,
        )
        paid = await self.fines.paid_totals(fine.id for fine in fines)
        items = [FineOut.from_fine(fine, paid.get(fine.id, ZERO)) for fine in fines]
        return Page.build(items, total, params)

    async def get(self, user: CurrentUser, fine_id: int) -> FineDetailOut:
        fine = await self.fines.get(fine_id, with_payments=True)
        # Khoan cua nguoi khac tra 404 nhu khong ton tai: READER khong do duoc
        # id nao co that.
        if fine is None or (not user.is_staff and fine.reader_id != user.reader_id):
            raise AppError(404, "not_found", "Khong tim thay khoan phat")
        return FineDetailOut.from_loaded(fine)

    async def outstanding(self, user: CurrentUser, reader_id: int) -> OutstandingOut:
        if not user.is_staff and reader_id != user.reader_id:
            raise AppError(403, "forbidden", "Chi xem duoc cong no cua chinh minh")
        count, amount = await self.fines.outstanding(reader_id)
        return OutstandingOut(
            reader_id=reader_id,
            unpaid_count=count,
            outstanding_amount=amount,
            has_outstanding=count > 0,
        )

    # --- Ghi (thu thu / admin) -----------------------------------------------

    async def create(self, user: CurrentUser, data: FineCreate) -> FineDetailOut:
        fine = Fine(
            reader_id=data.reader_id,
            loan_item_id=data.loan_item_id,
            fine_type=data.fine_type,
            amount=data.amount,
            status=FineStatus.UNPAID,
            notes=data.notes,
        )
        self.fines.add(fine)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            # readers/loan_items thuoc service khac, khong query thang duoc; FK
            # cua DB la thu kiem ban doc/luot muon co ton tai hay khong.
            await self.session.rollback()
            message = str(exc.orig)
            if "fk_fines_reader" in message:
                raise AppError(404, "reader_not_found", "Khong tim thay ban doc") from None
            if "fk_fines_item" in message:
                raise AppError(404, "loan_item_not_found", "Khong tim thay luot muon") from None
            raise
        await self.session.commit()
        return await self._detail(fine.id)

    async def pay(self, user: CurrentUser, fine_id: int, data: PaymentCreate) -> FineDetailOut:
        fine = await self._lock_unpaid(fine_id, "Khoan phat da thanh toan xong hoac da duoc mien")
        # Doc SAU khi da khoa: request song song phai cho o buoc khoa, toi day
        # thi payment cua no da commit va duoc cong vao.
        paid = await self.payments.paid_total(fine.id)
        remaining = fine.amount - paid
        if data.amount > remaining:
            raise AppError(
                409,
                "payment_exceeds_remaining",
                f"So tien nop vuot qua so con no ({remaining:.2f})",
            )

        self.payments.add(
            Payment(
                fine_id=fine.id,
                amount=data.amount,
                method=data.method,
                staff_id=user.id,
                notes=data.notes,
            )
        )
        if paid + data.amount >= fine.amount:
            fine.status = FineStatus.PAID
        try:
            await self.session.flush()
        except IntegrityError as exc:
            await self.session.rollback()
            if "fk_payments_staff" in str(exc.orig):
                raise AppError(
                    409, "staff_not_found", "Tai khoan thu thu khong con ton tai"
                ) from None
            raise
        await self.session.commit()
        return await self._detail(fine.id)

    async def waive(self, user: CurrentUser, fine_id: int, data: WaiveIn) -> FineDetailOut:
        fine = await self._lock_unpaid(fine_id, "Chi mien duoc khoan phat chua thanh toan")
        # Schema khong co cot ly do/nguoi mien: ghi vao notes, giu ghi chu cu.
        note = f"{WAIVE_PREFIX} {data.reason} (user #{user.id})"
        notes = f"{fine.notes} | {note}" if fine.notes else note
        if len(notes) > NOTES_MAX:
            raise AppError(
                409, "notes_too_long", "Ghi chu cua khoan phat da qua dai, hay rut gon ly do"
            )
        fine.notes = notes
        fine.status = FineStatus.WAIVED
        await self.session.commit()
        return await self._detail(fine.id)

    # --- Noi bo ------------------------------------------------------------

    async def _lock_unpaid(self, fine_id: int, not_unpaid_detail: str) -> Fine:
        fine = await self.fines.get(fine_id, for_update=True)
        if fine is None:
            raise AppError(404, "not_found", "Khong tim thay khoan phat")
        if fine.status != FineStatus.UNPAID:
            raise AppError(409, "fine_closed", not_unpaid_detail)
        return fine

    async def _detail(self, fine_id: int) -> FineDetailOut:
        fine = await self.fines.get(fine_id, with_payments=True)
        assert fine is not None  # vua ghi xong trong cung session
        return FineDetailOut.from_loaded(fine)
