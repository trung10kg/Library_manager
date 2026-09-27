"""/api/billing/readers/{id}/outstanding - circulation goi truoc khi cho muon."""

from __future__ import annotations

from tests.seed_ids import CLEAN_READER_ID, READER_ID

from app.models import FineStatus


def url(reader_id: int) -> str:
    return f"/api/billing/readers/{reader_id}/outstanding"


async def test_khong_token_401(client):
    assert (await client.get(url(1))).status_code == 401


async def test_tru_phan_da_nop_va_bo_khoan_da_dong(client, staff, make_fine):
    await make_fine(amount="50000")
    partly = await make_fine(amount="30000")
    await client.post(
        f"/api/billing/fines/{partly.id}/payments", json={"amount": "10000"}, headers=staff
    )
    await make_fine(amount="70000", status=FineStatus.PAID)
    await make_fine(amount="90000", status=FineStatus.WAIVED)

    resp = await client.get(url(CLEAN_READER_ID), headers=staff)

    assert resp.status_code == 200
    assert resp.json() == {
        "reader_id": CLEAN_READER_ID,
        "unpaid_count": 2,
        "outstanding_amount": "70000.00",
        "has_outstanding": True,
    }


async def test_khong_no(client, staff):
    resp = await client.get(url(CLEAN_READER_ID), headers=staff)
    body = resp.json()
    assert body["has_outstanding"] is False
    assert body["outstanding_amount"] == "0.00"


async def test_reader_xem_cua_minh(client, reader):
    resp = await client.get(url(READER_ID), headers=reader)
    assert resp.status_code == 200
    # Seed: fine 1 cua ban doc 1 = 52000, chua nop.
    assert resp.json()["outstanding_amount"] == "52000.00"


async def test_reader_xem_nguoi_khac_403(client, reader):
    resp = await client.get(url(CLEAN_READER_ID), headers=reader)
    assert resp.status_code == 403
