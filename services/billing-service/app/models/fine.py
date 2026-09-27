from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.db import Base

if TYPE_CHECKING:
    from app.models.payment import Payment


class FineType(StrEnum):
    """Khop ck_fines_type trong db/01_schema_mysql.sql."""

    OVERDUE = "OVERDUE"
    DAMAGE = "DAMAGE"
    LOST = "LOST"


class FineStatus(StrEnum):
    """Khop ck_fines_status sau migration 08: khong con PARTIAL. Tra mot phan
    van la UNPAID - so con no tinh tu payments."""

    UNPAID = "UNPAID"
    PAID = "PAID"
    WAIVED = "WAIVED"


class Fine(Base):
    __tablename__ = "fines"
    # MySQL khong co RETURNING: doc lai issued_at ngay sau INSERT.
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # loan_items thuoc circulation-service, readers thuoc reader-service. FK co
    # trong DB (fk_fines_item, fk_fines_reader) nhung khong khai bao o ORM: hai
    # bang do khong nam trong metadata cua service nay.
    loan_item_id: Mapped[int | None] = mapped_column(BigInteger)
    reader_id: Mapped[int] = mapped_column(BigInteger)
    fine_type: Mapped[str] = mapped_column(String(20))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default=FineStatus.UNPAID)
    issued_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    notes: Mapped[str | None] = mapped_column(String(300))

    # lazy="raise": luon selectinload(Fine.payments) truoc khi dung.
    payments: Mapped[list[Payment]] = relationship(
        back_populates="fine", lazy="raise", order_by="Payment.id"
    )
