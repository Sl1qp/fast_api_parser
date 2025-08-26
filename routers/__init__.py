from routers.refresh import refresh_router
from routers.trades import trades_router
from fastapi import APIRouter

main_router = APIRouter()
main_router.include_router(trades_router, tags=["trades"])
main_router.include_router(refresh_router, tags=["refresh"])
