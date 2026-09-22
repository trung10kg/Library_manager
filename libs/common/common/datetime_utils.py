"""Tien ich thoi gian.

MySQL kieu DATETIME khong luu offset mui gio: ghi mot datetime aware xuong
roi doc len se ra naive. Ca he thong quy uoc luu UTC, va dung cac ham o day
de gan/thao mui gio o bien - khong bao gio de datetime naive lot len tang
schema.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator


def utc_now() -> datetime:
    """Thoi diem hien tai, timezone-aware. Dung thay cho utcnow()."""
    return datetime.now(UTC)


def naive_utc_now() -> datetime:
    """Thoi diem hien tai dang naive UTC - de ghi hoac so sanh voi cot DATETIME."""
    return datetime.now(UTC).replace(tzinfo=None)


def as_utc(value: datetime | None) -> datetime | None:
    """Doc tu DB: gan UTC cho datetime naive, doi mui cho datetime aware."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def to_naive_utc(value: datetime | None) -> datetime | None:
    """Ghi xuong DB: quy ve UTC roi bo tzinfo cho khop kieu DATETIME."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


# Dung trong schema Out: gia tri naive doc tu MySQL duoc gan UTC truoc khi
# tra ra JSON, nen client luon nhan "...Z".
UtcDatetime = Annotated[datetime, AfterValidator(as_utc)]
