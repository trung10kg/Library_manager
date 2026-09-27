from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from app.models.fine import FineStatus, FineType
from app.models.payment import PaymentMethod
from common.datetime_utils import UtcDatetime
from common.pagination import Page

if TYPE_CHECKING:
    from app.models.fine import Fine

ZERO = Decimal("0.00")
_CENT = Decimal("0.01")

# Tien vao: khop DECIMAL(10,2) cua fines.amount / payments.amount. Phai > 0
# (ck_payments_amount); khoan phat 0 dong khong co nghia nen API cung chan.
MoneyIn = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
# Tien ra: luon 2 chu so thap phan, ke ca so tinh ra (SUM, hieu). Pydantic
# tra Decimal thanh chuoi trong JSON ("52000.00") - khong mat do chinh xac.
MoneyOut = Annotated[Decimal, AfterValidator(lambda v: v.quantize(_CENT))]

Notes = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


class FineCreate(BaseModel):
    reader_id: int = Field(gt=0)
    loan_item_id: int | None = Field(default=None, gt=0)
    fine_type: FineType
    amount: MoneyIn
    notes: Notes | None = None


class PaymentCreate(BaseModel):
    amount: MoneyIn
    method: PaymentMethod = PaymentMethod.CASH
    notes: Notes | None = None


class WaiveIn(BaseModel):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fine_id: int
    amount: MoneyOut
    method: PaymentMethod
    paid_at: UtcDatetime
    staff_id: int | None
    notes: str | None


class FineOut(BaseModel):
    id: int
    reader_id: int
    loan_item_id: int | None
    fine_type: FineType
    amount: MoneyOut
    status: FineStatus
    issued_at: UtcDatetime
    notes: str | None
    paid_total: MoneyOut
    # Con phai nop. PAID/WAIVED luon la 0: khoan da mien khong con no.
    remaining: MoneyOut

    @classmethod
    def fields_from(cls, fine: Fine, paid_total: Decimal) -> dict[str, object]:
        remaining = fine.amount - paid_total if fine.status == FineStatus.UNPAID else ZERO
        return {
            "id": fine.id,
            "reader_id": fine.reader_id,
            "loan_item_id": fine.loan_item_id,
            "fine_type": fine.fine_type,
            "amount": fine.amount,
            "status": fine.status,
            "issued_at": fine.issued_at,
            "notes": fine.notes,
            "paid_total": paid_total,
            "remaining": max(remaining, ZERO),
        }

    @classmethod
    def from_fine(cls, fine: Fine, paid_total: Decimal) -> FineOut:
        return cls(**cls.fields_from(fine, paid_total))


class FineDetailOut(FineOut):
    payments: list[PaymentOut]

    @classmethod
    def from_loaded(cls, fine: Fine) -> FineDetailOut:
        """fine.payments phai da duoc selectinload."""
        paid_total = sum((p.amount for p in fine.payments), ZERO)
        return cls(
            **cls.fields_from(fine, paid_total),
            payments=[PaymentOut.model_validate(p) for p in fine.payments],
        )


class OutstandingOut(BaseModel):
    """circulation-service goi truoc khi cho muon: has_outstanding = true thi
    tu choi voi outstanding_fines."""

    reader_id: int
    unpaid_count: int
    outstanding_amount: MoneyOut
    has_outstanding: bool


class PaymentPage(Page[PaymentOut]):
    # Tong tien cua MOI dong khop bo loc, khong chi trang hien tai.
    total_amount: MoneyOut


class PaymentFilter(BaseModel):
    from_date: date | None = None
    to_date: date | None = None
    method: PaymentMethod | None = None
    staff_id: int | None = None
    reader_id: int | None = None
