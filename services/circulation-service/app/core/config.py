from __future__ import annotations

from common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    SERVICE_NAME: str = "circulation-service"

    # Quy tac muon/tra KHONG nam o day: schema co bang loan_policies
    # quy dinh theo reader_type. Phase 4 doc tu DB.
    # Phase 4 them: CATALOG_URL, READER_URL, BILLING_URL.


settings = Settings()  # type: ignore[call-arg]
