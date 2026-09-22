from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from common.datetime_utils import as_utc, to_naive_utc, utc_now


def test_utc_now_co_timezone():
    now = utc_now()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_as_utc_gan_utc_cho_naive():
    """Gia tri doc tu MySQL DATETIME la naive va dang o UTC."""
    naive = datetime(2026, 3, 1, 8, 30)
    assert as_utc(naive) == datetime(2026, 3, 1, 8, 30, tzinfo=UTC)


def test_as_utc_doi_mui_cho_aware():
    hanoi = datetime(2026, 3, 1, 15, 30, tzinfo=timezone(timedelta(hours=7)))
    assert as_utc(hanoi) == datetime(2026, 3, 1, 8, 30, tzinfo=UTC)


def test_to_naive_utc_quy_ve_utc_roi_bo_tzinfo():
    hanoi = datetime(2026, 3, 1, 15, 30, tzinfo=timezone(timedelta(hours=7)))
    result = to_naive_utc(hanoi)
    assert result == datetime(2026, 3, 1, 8, 30)
    assert result.tzinfo is None


def test_none_di_qua_nguyen_ven():
    assert as_utc(None) is None
    assert to_naive_utc(None) is None


def test_utc_datetime_trong_schema_gan_utc():
    from pydantic import BaseModel

    from common.datetime_utils import UtcDatetime

    class Out(BaseModel):
        at: UtcDatetime

    out = Out(at=datetime(2026, 3, 1, 8, 30))
    assert out.at.tzinfo is not None
    assert out.model_dump_json() == '{"at":"2026-03-01T08:30:00Z"}'


def test_naive_utc_now():
    from common.datetime_utils import naive_utc_now

    now = naive_utc_now()
    assert now.tzinfo is None
    assert abs((utc_now().replace(tzinfo=None) - now).total_seconds()) < 5
