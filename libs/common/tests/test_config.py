from __future__ import annotations

import pytest
from pydantic import ValidationError

from common.config import BaseServiceSettings

URL = "mysql+aiomysql://root:1234@127.0.0.1:3306/library_db?charset=utf8mb4"


def test_doc_public_key_tu_chuoi():
    settings = BaseServiceSettings(DATABASE_URL=URL, JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----")
    assert settings.jwt_public_key.startswith("-----BEGIN")


def test_doc_public_key_tu_file(tmp_path, public_key):
    path = tmp_path / "jwt_public.pem"
    path.write_text(public_key, encoding="utf-8")
    settings = BaseServiceSettings(DATABASE_URL=URL, JWT_PUBLIC_KEY_PATH=path)
    assert settings.jwt_public_key == public_key


def test_thieu_ca_hai_nguon_key_thi_bao_loi():
    with pytest.raises(ValidationError):
        BaseServiceSettings(DATABASE_URL=URL)


def test_file_key_khong_ton_tai_bao_loi_ro_rang(tmp_path):
    settings = BaseServiceSettings(DATABASE_URL=URL, JWT_PUBLIC_KEY_PATH=tmp_path / "khong-co.pem")
    with pytest.raises(RuntimeError, match="task.py keys"):
        _ = settings.jwt_public_key


def test_thieu_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        BaseServiceSettings(JWT_PUBLIC_KEY="x")
