from fastapi import APIRouter

from app.api.routes import gemini, items
from app.invoices.router import router as invoices_router

api_router = APIRouter()
api_router.include_router(items.router)
api_router.include_router(gemini.router)
api_router.include_router(invoices_router)
