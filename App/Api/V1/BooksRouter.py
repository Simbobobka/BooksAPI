from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response, UploadFile, status

from App.Api.V1.Dependencies.GetCurrentUser import CurrentUser
from App.Api.V1.Dependencies.GetDbConnection import DbConnection
from App.Config.Settings import get_settings
from App.Schemas.Book.BookCreate import BookCreate
from App.Schemas.Book.BookListResponse import BookListResponse
from App.Schemas.Book.BookResponse import BookResponse
from App.Schemas.Book.BookUpdate import BookUpdate
from App.Schemas.Book.ImportResponse import ImportResponse
from App.Schemas.Book.WhatIfResponse import WhatIfResponse
from App.Services.Books.AiService import AiService
from App.Services.Books.BooksExporter import BooksExporter
from App.Services.Books.BooksImporter import BooksImporter
from App.Services.Books.BooksService import BooksService

router = APIRouter(prefix="/books", tags=["books"])

SortBy = Literal["title", "year", "created_at", "author"]
SortOrder = Literal["asc", "desc"]


@router.get("/", response_model=BookListResponse)
async def list_books(
    connection: DbConnection,
    title: Annotated[str | None, Query()] = None,
    genre_id: Annotated[int | None, Query()] = None,
    author: Annotated[str | None, Query()] = None,
    year_from: Annotated[int | None, Query(ge=1800)] = None,
    year_to: Annotated[int | None, Query(le=9999)] = None,
    sort_by: Annotated[SortBy, Query()] = "created_at",
    order: Annotated[SortOrder, Query()] = "asc",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> BookListResponse:
    return await BooksService(connection).list(
        title, genre_id, author, year_from, year_to, sort_by, order, limit, offset
    )


@router.get("/export")
async def export_books(
    connection: DbConnection,
    title: Annotated[str | None, Query()] = None,
    genre_id: Annotated[int | None, Query()] = None,
    author: Annotated[str | None, Query()] = None,
    year_from: Annotated[int | None, Query(ge=1800)] = None,
    year_to: Annotated[int | None, Query(le=9999)] = None,
    format: Annotated[Literal["json", "csv"], Query()] = "json",
) -> Response:
    books = await BooksService(connection).export(title, genre_id, author, year_from, year_to)
    if format == "csv":
        return Response(
            content=BooksExporter.to_csv(books),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=books.csv"},
        )
    return Response(
        content=BooksExporter.to_json(books),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=books.json"},
    )


@router.post("/import", response_model=ImportResponse)
async def import_books(
    file: UploadFile,
    connection: DbConnection,
    _: CurrentUser,
) -> ImportResponse:
    return await BooksImporter(connection).run(file)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, connection: DbConnection) -> BookResponse:
    return await BooksService(connection).get_by_id(book_id)


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookCreate,
    connection: DbConnection,
    _: CurrentUser,
) -> BookResponse:
    return await BooksService(connection).create(payload)


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    payload: BookUpdate,
    connection: DbConnection,
    _: CurrentUser,
) -> BookResponse:
    return await BooksService(connection).update(book_id, payload)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, connection: DbConnection, _: CurrentUser) -> None:
    await BooksService(connection).delete(book_id)


@router.get("/{book_id}/recommendations", response_model=list[BookResponse])
async def recommend_books(
    book_id: int,
    connection: DbConnection,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[BookResponse]:
    return await BooksService(connection).recommend(book_id, limit)


@router.get("/{book_id}/what-if", response_model=WhatIfResponse)
async def what_if(book_id: int, connection: DbConnection, _: CurrentUser) -> WhatIfResponse:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured",
        )
    book = await BooksService(connection).get_by_id(book_id)
    scenario = await AiService(settings.openai_api_key).what_if(book)
    return WhatIfResponse(scenario=scenario)
