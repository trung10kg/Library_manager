from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.db import Base

if TYPE_CHECKING:
    from app.models.fine import Fine


class PaymentMethod(StrEnum):
    """Khop ck_payments_method."""

    CASH = "CASH"
    TRANSFER = "TRANSFER"
    CARD = "CARD"


class Payment(Base):
    """Mot lan nop tien cho mot khoan phat. Khoan phat tra nhieu lan duoc."""

    __tablename__ = "payments"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fine_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("fines.id", ondelete="CASCADE"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    paid_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    method: Mapped[str] = mapped_column(String(20), default=PaymentMethod.CASH)
    # Thu thu thu tien. users thuoc auth-service - FK chi co o DB.
    staff_id: Mapped[int | None] = mapped_column(BigInteger)
    notes: Mapped[str | None] = mapped_column(String(300))

    fine: Mapped[Fine] = relationship(back_populates="payments", lazy="raise")
