"""/api/billing/payments - doi soat tien thu."""

from __future__ import annotations

import pytest
from tests.seed_ids import CLEAN_READER_ID, LIBRARIAN_ID

from common.datetime_utils import utc_now

URL = "/api/billing/payments"


@pytest.fixture
async def paid_today(client, staff, make_fine):
    """Hai lan nop hom nay cho ban doc sach: 15000 tien mat, 5000 chuyen khoan."""
    fine = await make_fine(amount="50000")
    pay = f"/api/billing/fines/{fine.id}/payments"
    await client.post(pay, json={"amount": "15000"}, headers=staff)
    await client.post(pay, json={"amount": "5000", "method": "TRANSFER"}, headers=staff)
    return fine


async def test_khong_token_401(client):
    assert (await client.get(URL)).status_code == 401


async def test_reader_403(client, reader):
    assert (await client.get(URL, headers=reader)).status_code == 403


async def test_seed_theo_khoang_ngay(client, staff):
    # Seed: 20000 ngay 2026-09-12 va 34000 ngay 2026-09-10.
    resp = await client.get(
        URL, params={"from_date": "2026-09-10", "to_date": "2026-09-12"}, headers=staff
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["total_amount"] == "54000.00"
    # Moi nhat truoc.
    assert [p["amount"] for p in body["items"]] == ["20000.00", "34000.00"]


async def test_to_date_bao_gom_ca_ngay(client, staff):
    resp = await client.get(
        URL, params={"from_date": "2026-09-12", "to_date": "2026-09-12"}, headers=staff
    )
    assert resp.json()["total_amount"] == "20000.00"


async def test_loc_theo_ban_doc_va_phuong_thuc(client, staff, paid_today):
    resp = await client.get(
        URL, params={"reader_id": CLEAN_READER_ID, "method": "CASH"}, headers=staff
    )

    body = resp.json()
    assert body["total"] == 1
    assert body["total_amount"] == "15000.00"
    assert body["items"][0]["staff_id"] == LIBRARIAN_ID


async def test_tong_tien_tinh_ca_cac_trang_khac(client, staff, paid_today):
    resp = await client.get(URL, params={"reader_id": CLEAN_READER_ID, "size": 1}, headers=staff)

    body = resp.json()
    assert len(body["items"]) == 1
    assert body["total"] == 2
    assert body["total_amount"] == "20000.00"


async def test_hom_nay_co_trong_khoang_ngay(client, staff, paid_today):
    today = utc_now().date().isoformat()
    resp = await client.get(
        URL,
        params={"from_date": today, "to_date": today, "reader_id": CLEAN_READER_ID},
        headers=staff,
    )
    assert resp.json()["total"] == 2


async def test_khoang_ngay_nguoc_422(client, staff):
    resp = await client.get(
        URL, params={"from_date": "2026-09-12", "to_date": "2026-09-01"}, headers=staff
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "invalid_date_range"
