from __future__ import annotations

from common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    SERVICE_NAME: str = "reader-service"


settings = Settings()  # type: ignore[call-arg]
