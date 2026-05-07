import csv
import io
import json

from App.Schemas.Book.BookResponse import BookResponse


class BooksExporter:
    @staticmethod
    def to_json(books: list[BookResponse]) -> str:
        return json.dumps([b.model_dump(mode="json") for b in books], indent=2)

    @staticmethod
    def to_csv(books: list[BookResponse]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "title",
                "published_year",
                "genre_id",
                "genre_name",
                "author_name",
                "author_last_name",
                "author_middle_name",
                "author_pen_name",
                "created_at",
                "updated_at",
            ]
        )
        for book in books:
            for author in book.authors:
                writer.writerow(
                    [
                        book.id,
                        book.title,
                        book.published_year,
                        book.genre.id,
                        book.genre.name,
                        author.name,
                        author.last_name or "",
                        author.middle_name or "",
                        author.pen_name or "",
                        book.created_at.isoformat(),
                        book.updated_at.isoformat(),
                    ]
                )
        return output.getvalue()
