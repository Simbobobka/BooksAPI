import csv
import io
import json

from asyncpg import Connection
from fastapi import HTTPException, UploadFile
from pydantic import ValidationError

from App.Schemas.Book.BookCreate import BookCreate
from App.Schemas.Book.ImportResponse import ImportResponse, ImportRowError
from App.Services.Books.BooksService import BooksService


class BooksImporter:
    def __init__(self, connection: Connection) -> None:
        self._service = BooksService(connection)

    async def run(self, file: UploadFile) -> ImportResponse:
        content = await file.read()
        filename = file.filename or ""

        if filename.endswith(".csv") or (file.content_type or "").startswith("text/csv"):
            rows, errors = self._parse_csv(content)
        else:
            rows, errors = self._parse_json(content)

        imported = 0
        for row_num, book_create in rows:
            try:
                await self._service.create(book_create)
                imported += 1
            except HTTPException as e:
                errors.append(ImportRowError(row=row_num, detail=e.detail))
            except Exception as e:
                errors.append(ImportRowError(row=row_num, detail=str(e)))

        errors.sort(key=lambda e: e.row)
        return ImportResponse(imported=imported, failed=len(errors), errors=errors)

    @staticmethod
    def _parse_json(content: bytes) -> tuple[list[tuple[int, BookCreate]], list[ImportRowError]]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return [], [ImportRowError(row=0, detail=f"Invalid JSON: {e}")]

        if not isinstance(data, list):
            return [], [ImportRowError(row=0, detail="JSON root must be an array")]

        rows: list[tuple[int, BookCreate]] = []
        errors: list[ImportRowError] = []
        for i, item in enumerate(data, start=1):
            try:
                rows.append((i, BookCreate.model_validate(item)))
            except ValidationError as e:
                errors.append(ImportRowError(row=i, detail=e.errors()[0]["msg"]))

        return rows, errors

    @staticmethod
    def _parse_csv(content: bytes) -> tuple[list[tuple[int, BookCreate]], list[ImportRowError]]:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return [], [ImportRowError(row=0, detail="File must be UTF-8 encoded")]

        rows: list[tuple[int, BookCreate]] = []
        errors: list[ImportRowError] = []

        reader = csv.DictReader(io.StringIO(text))
        current_key: tuple | None = None
        current_start_row = 0
        current_book: dict | None = None
        current_authors: list[dict] = []

        def flush() -> None:
            if current_book is None:
                return
            try:
                rows.append((current_start_row, BookCreate.model_validate(current_book)))
            except ValidationError as e:
                errors.append(ImportRowError(row=current_start_row, detail=e.errors()[0]["msg"]))

        def col(raw: dict, name: str) -> str:
            return (raw.get(name) or "").strip()

        for i, raw in enumerate(reader, start=1):
            key = (col(raw, "title"), col(raw, "published_year"), col(raw, "genre_id"))
            author = {
                "name": col(raw, "author_name") or None,
                "last_name": col(raw, "author_last_name") or None,
                "middle_name": col(raw, "author_middle_name") or None,
                "pen_name": col(raw, "author_pen_name") or None,
            }

            if key == current_key:
                current_authors.append(author)
                current_book["authors"] = current_authors  # type: ignore[index]
            else:
                flush()
                current_key = key
                current_start_row = i
                current_authors = [author]
                current_book = {
                    "title": key[0],
                    "published_year": key[1],
                    "genre_id": key[2],
                    "authors": current_authors,
                }

        flush()
        return rows, errors
