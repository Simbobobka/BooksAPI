from asyncpg import Connection, Record
from fastapi import HTTPException, status

from App.Repositories.AuthorsRepository import AuthorsRepository
from App.Repositories.BooksRepository import BooksRepository
from App.Repositories.GenresRepository import GenresRepository
from App.Schemas.Author.AuthorBase import AuthorBase
from App.Schemas.Author.AuthorResponse import AuthorResponse
from App.Schemas.Book.BookCreate import BookCreate
from App.Schemas.Book.BookListResponse import BookListResponse
from App.Schemas.Book.BookResponse import BookResponse
from App.Schemas.Book.BookUpdate import BookUpdate
from App.Schemas.Genre.GenreResponse import GenreResponse


class BooksService:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection
        self._books = BooksRepository(connection)
        self._authors = AuthorsRepository(connection)
        self._genres = GenresRepository(connection)

    def _build_response(self, book: Record, author_records: list[Record]) -> BookResponse:
        return BookResponse(
            id=book["id"],
            title=book["title"],
            published_year=book["published_year"],
            genre=GenreResponse(id=book["genre_id"], name=book["genre_name"]),
            authors=[
                AuthorResponse(
                    id=r["id"],
                    name=r["name"],
                    last_name=r["last_name"],
                    middle_name=r["middle_name"],
                    pen_name=r["pen_name"],
                )
                for r in author_records
            ],
            created_at=book["created_at"],
            updated_at=book["updated_at"],
        )

    async def _validate_genre(self, genre_id: int) -> None:
        if await self._genres.get_by_id(genre_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Genre with id={genre_id} not found",
            )

    async def _upsert_authors(self, authors: list[AuthorBase]) -> list[int]:
        ids: list[int] = []
        for a in authors:
            record = await self._authors.get_or_create(
                a.name, a.last_name, a.middle_name, a.pen_name
            )
            ids.append(record["id"])
        return ids

    async def create(self, payload: BookCreate) -> BookResponse:
        await self._validate_genre(payload.genre_id)
        async with self._connection.transaction():
            book = await self._books.create(payload.title, payload.published_year, payload.genre_id)
            author_ids = await self._upsert_authors(payload.authors)
            await self._books.set_authors(book["id"], author_ids)
        author_records = await self._authors.get_by_book_ids([book["id"]])
        return self._build_response(book, author_records)

    async def get_by_id(self, book_id: int) -> BookResponse:
        book = await self._books.get_by_id(book_id)
        if book is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        author_records = await self._authors.get_by_book_ids([book_id])
        return self._build_response(book, author_records)

    async def list(
        self,
        title: str | None,
        genre_id: int | None,
        author: str | None,
        year_from: int | None,
        year_to: int | None,
        sort_by: str,
        order: str,
        limit: int,
        offset: int,
    ) -> BookListResponse:
        book_records, total = await self._books.list(
            title, genre_id, author, year_from, year_to, sort_by, order, limit, offset
        )
        if not book_records:
            return BookListResponse(items=[], total=total, limit=limit, offset=offset)
        book_ids = [r["id"] for r in book_records]
        all_authors = await self._authors.get_by_book_ids(book_ids)
        authors_map: dict[int, list[Record]] = {bid: [] for bid in book_ids}
        for ar in all_authors:
            authors_map[ar["book_id"]].append(ar)
        items = [self._build_response(br, authors_map[br["id"]]) for br in book_records]
        return BookListResponse(items=items, total=total, limit=limit, offset=offset)

    async def update(self, book_id: int, payload: BookUpdate) -> BookResponse:
        if await self._books.get_by_id(book_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        if payload.genre_id is not None:
            await self._validate_genre(payload.genre_id)
        async with self._connection.transaction():
            book = await self._books.update(
                book_id,
                title=payload.title,
                published_year=payload.published_year,
                genre_id=payload.genre_id,
            )
            if payload.authors is not None:
                author_ids = await self._upsert_authors(payload.authors)
                await self._books.set_authors(book_id, author_ids)
        author_records = await self._authors.get_by_book_ids([book_id])
        return self._build_response(book, author_records)

    async def export(
        self,
        title: str | None,
        genre_id: int | None,
        author: str | None,
        year_from: int | None,
        year_to: int | None,
    ) -> list[BookResponse]:
        book_records = await self._books.export(title, genre_id, author, year_from, year_to)
        if not book_records:
            return []
        book_ids = [r["id"] for r in book_records]
        all_authors = await self._authors.get_by_book_ids(book_ids)
        authors_map: dict[int, list[Record]] = {bid: [] for bid in book_ids}
        for ar in all_authors:
            authors_map[ar["book_id"]].append(ar)
        return [self._build_response(br, authors_map[br["id"]]) for br in book_records]

    async def delete(self, book_id: int) -> None:
        if not await self._books.delete(book_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
