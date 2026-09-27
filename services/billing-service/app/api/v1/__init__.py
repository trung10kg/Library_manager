from fastapi import APIRouter

from app.api.v1 import fines, payments, readers

# Router goc cua billing-service, mount duoi /api/billing trong main.py.
router = APIRouter()
router.include_router(fines.router)
router.include_router(payments.router)
router.include_router(readers.router)
