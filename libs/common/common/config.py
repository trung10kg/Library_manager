"""Settings goc cho moi service.

Settings cua tung service ke thua lop nay va them cai rieng cua no. Cac quy
tac nghiep vu (so cuon toi da, han muon, tien phat...) KHONG nam o day: schema
da co bang `loan_policies` quy dinh theo reader_type, circulation-service doc
tu DB.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    SERVICE_NAME: str = "library-service"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str
    RABBITMQ_URL: str = ""

    # Mot trong hai: duong dan file PEM, hoac noi dung PEM (dung trong test).
    JWT_PUBLIC_KEY_PATH: Path | None = None
    JWT_PUBLIC_KEY: str | None = None

    @model_validator(mode="after")
    def _check_jwt_source(self) -> BaseServiceSettings:
        if self.JWT_PUBLIC_KEY is None and self.JWT_PUBLIC_KEY_PATH is None:
            raise ValueError("Can JWT_PUBLIC_KEY_PATH hoac JWT_PUBLIC_KEY")
        return self

    @property
    def jwt_public_key(self) -> str:
        if self.JWT_PUBLIC_KEY:
            return self.JWT_PUBLIC_KEY
        assert self.JWT_PUBLIC_KEY_PATH is not None  # model_validator da dam bao
        if not self.JWT_PUBLIC_KEY_PATH.exists():
            raise RuntimeError(
                f"Khong tim thay public key tai {self.JWT_PUBLIC_KEY_PATH}. "
                "Chay: python task.py keys"
            )
        return self.JWT_PUBLIC_KEY_PATH.read_text(encoding="utf-8")
