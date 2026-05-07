from fastapi import APIRouter

from App.Api.V1.AuthRouter import router as auth_router
from App.Api.V1.BooksRouter import router as books_router
from App.Api.V1.GenresRouter import router as genres_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(genres_router)
router.include_router(books_router)
