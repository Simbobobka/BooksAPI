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
        for i, raw in enumerate(reader, start=1):
            try:
                rows.append((i, BooksImporter._csv_row_to_book(raw)))
            except (ValidationError, ValueError) as e:
                msg = e.errors()[0]["msg"] if isinstance(e, ValidationError) else str(e)
                errors.append(ImportRowError(row=i, detail=msg))

        return rows, errors

    @staticmethod
    def _csv_row_to_book(raw: dict[str, str]) -> BookCreate:
        authors_raw = (raw.get("authors") or "").strip()
        authors: list[dict] = []
        for entry in authors_raw.split(";"):
            entry = entry.strip()
            if not entry:
                continue
            parts = [p.strip() or None for p in entry.split("|")]
            while len(parts) < 4:
                parts.append(None)
            authors.append(
                {
                    "name": parts[0],
                    "last_name": parts[1],
                    "middle_name": parts[2],
                    "pen_name": parts[3],
                }
            )

        return BookCreate.model_validate(
            {
                "title": (raw.get("title") or "").strip(),
                "published_year": (raw.get("published_year") or "").strip(),
                "genre_id": (raw.get("genre_id") or "").strip(),
                "authors": authors,
            }
        )
