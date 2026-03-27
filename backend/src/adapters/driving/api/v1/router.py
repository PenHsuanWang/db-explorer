from fastapi import APIRouter

from src.adapters.driving.api.v1.auth import router as auth_router
from src.adapters.driving.api.v1.connections import router as connections_router
from src.adapters.driving.api.v1.peek import router as peek_router
from src.adapters.driving.api.v1.search import router as search_router
from src.adapters.driving.api.v1.workbench import router as workbench_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(connections_router)
router.include_router(search_router)
router.include_router(peek_router)
router.include_router(workbench_router)
