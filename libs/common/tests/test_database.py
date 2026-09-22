"""Duong ket noi database that: driver aiomysql, nap schema, mui gio UTC.

Chay tren DB rieng `library_test_db`, khong dung toi `library_db`.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from common.datetime_utils import as_utc
from common.db import configure_database, dispose_database
from common.testing import load_schema

DATABASE_URL = os.environ.get("DATABASE_URL", "")

requires_mysql = pytest.mark.skipif(
    not DATABASE_URL.startswith("mysql+aiomysql://"),
    reason="Can DATABASE_URL tro toi MySQL test - chay bang: python task.py test",
)


def test_load_schema_tu_choi_database_khong_phai_test():
    """Chot chan quan trong nhat trong repo.

    db/01_schema_mysql.sql mo dau bang DROP DATABASE. Neu mot lan chay pytest
    sai cau hinh tro vao library_db, toan bo du lieu that se mat. Ham phai
    tu choi TRUOC khi goi toi client mysql.
    """
    with pytest.raises(RuntimeError, match="_test_db"):
        load_schema("mysql+aiomysql://root:1234@127.0.0.1:3306/library_db")

    with pytest.raises(RuntimeError, match="_test_db"):
        load_schema("mysql+aiomysql://root:1234@127.0.0.1:3306/production")


@pytest.fixture(scope="module")
def schema() -> None:
    load_schema(DATABASE_URL)


@pytest.fixture
async def engine(schema: None):
    eng = configure_database(DATABASE_URL)
    yield eng
    await dispose_database()


@requires_mysql
async def test_ket_noi_duoc(engine):
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT 1"))).scalar_one() == 1


@requires_mysql
async def test_session_chay_o_utc(engine):
    """init_command phai co tac dung, neu khong NOW() se theo gio may chu."""
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT @@session.time_zone"))).scalar_one() == "+00:00"


@requires_mysql
async def test_schema_va_seed_da_nap(engine):
    async with engine.connect() as conn:
        tables = (
            await conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE'"
                )
            )
        ).scalar_one()
        assert tables == 20

        # Trigger va view cung phai co - day la ly do phai nap qua client
        # mysql chu khong qua metadata.create_all().
        triggers = (
            await conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.triggers "
                    "WHERE trigger_schema = DATABASE()"
                )
            )
        ).scalar_one()
        assert triggers == 6

        views = (
            await conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = DATABASE()"
                )
            )
        ).scalar_one()
        assert views == 3

        assert (await conn.execute(text("SELECT COUNT(*) FROM books"))).scalar_one() == 40
        assert (await conn.execute(text("SELECT COUNT(*) FROM book_copies"))).scalar_one() == 100


@requires_mysql
async def test_tieng_viet_co_dau_khong_hong(engine):
    async with engine.connect() as conn:
        name = (await conn.execute(text("SELECT full_name FROM readers WHERE id = 1"))).scalar_one()
    assert name == "Nguyễn Văn An"


@requires_mysql
async def test_datetime_doc_len_la_naive_va_as_utc_gan_lai_mui(engine):
    """MySQL DATETIME khong luu offset - day la ly do co datetime_utils."""
    async with engine.connect() as conn:
        value = (await conn.execute(text("SELECT created_at FROM users WHERE id = 1"))).scalar_one()

    assert value.tzinfo is None, "MySQL tra ve naive - dung as_utc() truoc khi dua ra schema"
    assert as_utc(value).tzinfo is not None
