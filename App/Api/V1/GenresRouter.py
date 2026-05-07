from fastapi import APIRouter

from App.Api.V1.Dependencies.GetDbConnection import DbConnection
from App.Repositories.GenresRepository import GenresRepository
from App.Schemas.Genre.GenreResponse import GenreResponse

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("/", response_model=list[GenreResponse])
async def list_genres(connection: DbConnection) -> list[GenreResponse]:
    records = await GenresRepository(connection).get_all()
    return [GenreResponse(id=r["id"], name=r["name"]) for r in records]
