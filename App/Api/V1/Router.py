from fastapi import APIRouter

from App.Api.V1.AuthRouter import router as auth_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
