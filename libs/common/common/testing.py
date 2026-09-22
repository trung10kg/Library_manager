"""Tien ich dung trong test cua ca 5 service.

Khong import trong code chay that.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.engine import make_url

# Ten database trong db/*.sql. load_schema thay bang ten DB test.
SOURCE_DB_NAME = "library_db"

# Nen ban dau. 05_verify.sql co y vi pham rang buoc nen khong nam o day.
SCHEMA_FILES = (
    "01_schema_mysql.sql",
    "02_triggers.sql",
    "03_views.sql",
    "04_seed.sql",
)

MYSQL_FALLBACK = Path(r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe")


def generate_rsa_keypair(key_size: int = 2048) -> tuple[str, str]:
    """(private_pem, public_pem) cho test. 2048 bit giong key that - PyJWT
    canh bao neu ngan hon."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    private = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public = (
        key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private, public


def mysql_client() -> str:
    found = shutil.which("mysql")
    if found:
        return found
    if MYSQL_FALLBACK.exists():
        return str(MYSQL_FALLBACK)
    raise RuntimeError("Khong tim thay client 'mysql'. Them thu muc bin cua MySQL vao PATH.")


def schema_directory(schema_dir: Path | str | None = None) -> Path:
    directory = Path(schema_dir or os.environ.get("SCHEMA_DIR") or "db")
    if not directory.is_dir():
        raise RuntimeError(f"Khong thay thu muc schema: {directory}")
    return directory


def load_schema(database_url: str, schema_dir: Path | str | None = None) -> None:
    """Dung lai schema + seed vao DATABASE TEST tu db/*.sql.

    Phai shell ra client mysql chu khong chay qua driver: 02_triggers.sql
    dung lenh DELIMITER, von la chi thi cua client chu khong phai SQL.

    db/01_schema_mysql.sql mo dau bang DROP DATABASE. Ham nay tu choi chay
    neu ten DB khong ket thuc bang "_test_db" - do la thu duy nhat chan mot
    lan chay pytest sai cau hinh khoi xoa sach library_db that.
    """
    url = make_url(database_url)
    db_name = url.database
    if not db_name or not db_name.endswith("_test_db"):
        raise RuntimeError(
            f"load_schema tu choi database {db_name!r}: ten phai ket thuc bang '_test_db'."
        )

    directory = schema_directory(schema_dir)
    base_cmd = [
        mysql_client(),
        f"-h{url.host or '127.0.0.1'}",
        f"-P{url.port or 3306}",
        f"-u{url.username}",
        f"-p{url.password}",
        "--default-character-set=utf8mb4",
    ]
    pattern = re.compile(rf"\b{re.escape(SOURCE_DB_NAME)}\b")

    for name in SCHEMA_FILES:
        _run_sql_file(directory / name, base_cmd, pattern, db_name)


def _run_sql_file(path: Path, cmd: list[str], pattern: re.Pattern[str], db_name: str) -> None:
    sql = pattern.sub(db_name, path.read_text(encoding="utf-8"))
    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".sql", delete=False, encoding="utf-8", newline="\n"
    )
    try:
        tmp.write(sql)
        tmp.close()
        with open(tmp.name, "rb") as fh:
            proc = subprocess.run(cmd, stdin=fh, capture_output=True)
        if proc.returncode != 0:
            raise RuntimeError(f"Nap {path.name} that bai:\n{proc.stderr.decode(errors='replace')}")
    finally:
        os.unlink(tmp.name)
