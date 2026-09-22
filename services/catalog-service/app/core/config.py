from __future__ import annotations

from common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    SERVICE_NAME: str = "catalog-service"


settings = Settings()  # type: ignore[call-arg]
