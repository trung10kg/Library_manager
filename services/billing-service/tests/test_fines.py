"""/api/billing/fines - xem, lap, nop tien, mien phat."""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import func, select
from tests.seed_ids import CLEAN_READER_ID, LIBRARIAN_ID, READER_ID

from app.models import FineStatus, Payment
from common.security import Role

URL = "/api/billing/fines"


def fine_body(**overrides) -> dict:
    data = {"reader_id": CLEAN_READER_ID, "fine_type": "DAMAGE", "amount": "80000"}
    data.update(overrides)
    return data


# --- Phan quyen -------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("GET", URL),
        ("GET", f"{URL}/1"),
        ("POST", URL),
        ("POST", f"{URL}/1/payments"),
        ("POST", f"{URL}/1/waive"),
    ],
)
async def test_khong_token_401(client, method, url):
    resp = await client.request(method, url, json={})
    assert resp.status_code == 401
    assert resp.json()["code"] == "not_authenticated"


@pytest.mark.parametrize(
    ("url", "body"),
    [
        (URL, fine_body()),
        (f"{URL}/1/payments", {"amount": "1000"}),
        (f"{URL}/1/waive", {"reason": "Hoan canh kho khan"}),
    ],
)
async def test_reader_khong_duoc_ghi_403(client, reader, url, body):
    resp = await client.post(url, json=body, headers=reader)
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"


async def test_thu_thu_khong_duoc_mien_phat_403(client, staff, make_fine):
    fine = await make_fine()
    resp = await client.post(f"{URL}/{fine.id}/waive", json={"reason": "Ly do"}, headers=staff)
    assert resp.status_code == 403


# --- Xem --------------------------------------------------------------------


async def test_thu_thu_xem_danh_sach_loc_theo_ban_doc(client, staff, make_fine):
    await make_fine(amount="10000")
    await make_fine(amount="20000", status=FineStatus.PAID)

    resp = await client.get(URL, params={"reader_id": CLEAN_READER_ID}, headers=staff)

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert {f["reader_id"] for f in body["items"]} == {CLEAN_READER_ID}


async def test_loc_theo_trang_thai(client, staff, make_fine):
    await make_fine(status=FineStatus.PAID)
    await make_fine(status=FineStatus.UNPAID)

    resp = await client.get(
        URL, params={"reader_id": CLEAN_READER_ID, "status": "PAID"}, headers=staff
    )

    assert [f["status"] for f in resp.json()["items"]] == ["PAID"]


async def test_reader_chi_thay_khoan_cua_minh(client, reader, make_fine):
    await make_fine(reader_id=CLEAN_READER_ID)  # cua nguoi khac

    resp = await client.get(URL, headers=reader)

    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items, "seed co khoan phat cua ban doc 1"
    assert {f["reader_id"] for f in items} == {READER_ID}


async def test_reader_hoi_danh_sach_nguoi_khac_403(client, reader):
    resp = await client.get(URL, params={"reader_id": CLEAN_READER_ID}, headers=reader)
    assert resp.status_code == 403


async def test_reader_chua_co_ho_so_thay_danh_sach_rong(client, headers):
    resp = await client.get(URL, headers=headers([Role.READER], user_id=13, reader_id=None))
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_chi_tiet_co_lich_su_nop_va_so_con_no(client, staff):
    # Seed: fine 2 = 42000, da nop 20000.
    resp = await client.get(f"{URL}/2", headers=staff)

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "UNPAID"
    assert body["amount"] == "42000.00"
    assert body["paid_total"] == "20000.00"
    assert body["remaining"] == "22000.00"
    assert [p["amount"] for p in body["payments"]] == ["20000.00"]


async def test_reader_xem_khoan_cua_nguoi_khac_404(client, reader, make_fine):
    fine = await make_fine(reader_id=CLEAN_READER_ID)
    resp = await client.get(f"{URL}/{fine.id}", headers=reader)
    assert resp.status_code == 404


async def test_reader_xem_khoan_cua_minh(client, reader, make_fine):
    fine = await make_fine(reader_id=READER_ID)
    resp = await client.get(f"{URL}/{fine.id}", headers=reader)
    assert resp.status_code == 200


async def test_khoan_khong_ton_tai_404(client, staff):
    resp = await client.get(f"{URL}/999999", headers=staff)
    assert resp.status_code == 404
    assert resp.json()["code"] == "not_found"


# --- Lap khoan phat -------------------------------------------------------------


async def test_lap_khoan_phat(client, staff):
    resp = await client.post(URL, json=fine_body(notes="  Rach bia  "), headers=staff)

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "UNPAID"
    assert body["amount"] == "80000.00"
    assert body["remaining"] == "80000.00"
    assert body["notes"] == "Rach bia"
    assert body["payments"] == []
    assert body["issued_at"].endswith("Z")


async def test_lap_phat_ban_doc_khong_ton_tai_404(client, staff):
    resp = await client.post(URL, json=fine_body(reader_id=999999), headers=staff)
    assert resp.status_code == 404
    assert resp.json()["code"] == "reader_not_found"


async def test_lap_phat_luot_muon_khong_ton_tai_404(client, staff):
    resp = await client.post(URL, json=fine_body(loan_item_id=999999), headers=staff)
    assert resp.status_code == 404
    assert resp.json()["code"] == "loan_item_not_found"


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount": "0"},
        {"amount": "-5000"},
        {"amount": "100.001"},
        {"amount": "123456789.00"},
        {"fine_type": "OTHER"},
        {"reader_id": 0},
    ],
)
async def test_lap_phat_du_lieu_sai_422(client, staff, overrides):
    resp = await client.post(URL, json=fine_body(**overrides), headers=staff)
    assert resp.status_code == 422
    assert resp.json()["code"] == "validation_error"


# --- Nop tien ---------------------------------------------------------------


async def test_nop_mot_phan_van_unpaid(client, session, staff, make_fine):
    fine = await make_fine(amount="50000")

    resp = await client.post(
        f"{URL}/{fine.id}/payments", json={"amount": "20000", "method": "TRANSFER"}, headers=staff
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "UNPAID"
    assert body["paid_total"] == "20000.00"
    assert body["remaining"] == "30000.00"
    payment = body["payments"][0]
    assert payment["method"] == "TRANSFER"
    assert payment["staff_id"] == LIBRARIAN_ID


async def test_nop_du_thi_chuyen_paid(client, staff, make_fine):
    fine = await make_fine(amount="50000")
    await client.post(f"{URL}/{fine.id}/payments", json={"amount": "20000"}, headers=staff)

    resp = await client.post(f"{URL}/{fine.id}/payments", json={"amount": "30000"}, headers=staff)

    body = resp.json()
    assert body["status"] == "PAID"
    assert body["remaining"] == "0.00"
    assert len(body["payments"]) == 2


async def test_nop_vuot_so_con_no_409(client, session, staff, make_fine):
    fine = await make_fine(amount="50000")

    resp = await client.post(
        f"{URL}/{fine.id}/payments", json={"amount": "50000.01"}, headers=staff
    )

    assert resp.status_code == 409
    assert resp.json()["code"] == "payment_exceeds_remaining"
    count = await session.scalar(select(func.count()).where(Payment.fine_id == fine.id))
    assert count == 0


@pytest.mark.parametrize("status", [FineStatus.PAID, FineStatus.WAIVED])
async def test_nop_vao_khoan_da_dong_409(client, staff, make_fine, status):
    fine = await make_fine(status=status)
    resp = await client.post(f"{URL}/{fine.id}/payments", json={"amount": "1000"}, headers=staff)
    assert resp.status_code == 409
    assert resp.json()["code"] == "fine_closed"


async def test_nop_khoan_khong_ton_tai_404(client, staff):
    resp = await client.post(f"{URL}/999999/payments", json={"amount": "1000"}, headers=staff)
    assert resp.status_code == 404


async def test_nop_phuong_thuc_la_422(client, staff, make_fine):
    fine = await make_fine()
    resp = await client.post(
        f"{URL}/{fine.id}/payments", json={"amount": "1000", "method": "BITCOIN"}, headers=staff
    )
    assert resp.status_code == 422


async def test_hai_thu_thu_nop_cung_luc_khong_nop_du(real_env, staff):
    """Hai request nop du so tien cung luc: dung mot cai thanh cong."""
    fine = await real_env.create_fine("30000")
    url = f"{URL}/{fine.id}/payments"

    responses = await asyncio.gather(
        real_env.client.post(url, json={"amount": "30000"}, headers=staff),
        real_env.client.post(url, json={"amount": "30000"}, headers=staff),
    )

    assert sorted(r.status_code for r in responses) == [201, 409]
    async with real_env.factory() as s:
        paid = await s.scalar(select(func.sum(Payment.amount)).where(Payment.fine_id == fine.id))
    assert str(paid) == "30000.00"


# --- Mien phat --------------------------------------------------------------


async def test_admin_mien_phat(client, admin, make_fine):
    fine = await make_fine(amount="50000", notes="Lam uot sach")
    await client.post(  # da nop mot phan truoc khi mien
        f"{URL}/{fine.id}/payments", json={"amount": "10000"}, headers=admin
    )

    resp = await client.post(
        f"{URL}/{fine.id}/waive", json={"reason": "Hoan canh kho khan"}, headers=admin
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "WAIVED"
    assert body["remaining"] == "0.00"
    assert body["paid_total"] == "10000.00"
    assert body["notes"].startswith("Lam uot sach | [Mien phat] Hoan canh kho khan")


async def test_mien_khoan_da_tra_409(client, admin, make_fine):
    fine = await make_fine(status=FineStatus.PAID)
    resp = await client.post(f"{URL}/{fine.id}/waive", json={"reason": "Ly do"}, headers=admin)
    assert resp.status_code == 409
    assert resp.json()["code"] == "fine_closed"


async def test_mien_ly_do_qua_ngan_422(client, admin, make_fine):
    fine = await make_fine()
    resp = await client.post(f"{URL}/{fine.id}/waive", json={"reason": " x "}, headers=admin)
    assert resp.status_code == 422


async def test_mien_khi_ghi_chu_da_day_409(client, admin, make_fine):
    fine = await make_fine(notes="a" * 290)
    resp = await client.post(
        f"{URL}/{fine.id}/waive", json={"reason": "Hoan canh kho khan"}, headers=admin
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "notes_too_long"
