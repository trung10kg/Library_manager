from __future__ import annotations

from common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    SERVICE_NAME: str = "billing-service"

    # Phase 4 them: CIRCULATION_URL.


settings = Settings()  # type: ignore[call-arg]
