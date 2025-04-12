from fastapi import APIRouter
from src.api.endpoints import router as movies_router

main_router = APIRouter()

main_router.include_router(movies_router)
