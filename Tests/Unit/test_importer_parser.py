import json

from App.Services.Books.BooksImporter import BooksImporter


def test_parse_json_valid():
    data = [{"title": "Book", "published_year": 2020, "genre_id": 1, "authors": [{"name": "Alice"}]}]
    rows, errors = BooksImporter._parse_json(json.dumps(data).encode())
    assert len(rows) == 1
    assert len(errors) == 0
    assert rows[0][1].title == "Book"
    assert rows[0][0] == 1


def test_parse_json_invalid_item():
    data = [{"title": "No Authors", "published_year": 2020, "genre_id": 1}]
    rows, errors = BooksImporter._parse_json(json.dumps(data).encode())
    assert len(rows) == 0
    assert len(errors) == 1
    assert errors[0].row == 1


def test_parse_json_not_array():
    _, errors = BooksImporter._parse_json(b'{"title": "single"}')
    assert errors[0].detail == "JSON root must be an array"


def test_parse_json_malformed():
    _, errors = BooksImporter._parse_json(b"not json at all")
    assert errors[0].row == 0
    assert "Invalid JSON" in errors[0].detail


def test_parse_json_partial():
    data = [
        {"title": "Good", "published_year": 2020, "genre_id": 1, "authors": [{"name": "X"}]},
        {"title": "Bad"},
    ]
    rows, errors = BooksImporter._parse_json(json.dumps(data).encode())
    assert len(rows) == 1
    assert len(errors) == 1


def test_parse_csv_single_author():
    csv = (
        "title,published_year,genre_id,author_name,author_last_name,author_middle_name,author_pen_name\n"
        "My Book,2020,1,John,Doe,Middle,Pen\n"
    ).encode()
    rows, errors = BooksImporter._parse_csv(csv)
    assert len(rows) == 1
    assert len(errors) == 0
    author = rows[0][1].authors[0]
    assert author.name == "John"
    assert author.last_name == "Doe"
    assert author.middle_name == "Middle"
    assert author.pen_name == "Pen"


def test_parse_csv_empty_optional_fields():
    csv = (
        "title,published_year,genre_id,author_name,author_last_name,author_middle_name,author_pen_name\n"
        "Book,2020,1,Jane,,,\n"
    ).encode()
    rows, _ = BooksImporter._parse_csv(csv)
    author = rows[0][1].authors[0]
    assert author.last_name is None
    assert author.middle_name is None
    assert author.pen_name is None


def test_parse_csv_multi_author_grouping():
    csv = (
        "title,published_year,genre_id,author_name,author_last_name,author_middle_name,author_pen_name\n"
        "Shared,2020,1,Alice,Smith,,\n"
        "Shared,2020,1,Bob,Jones,,\n"
    ).encode()
    rows, errors = BooksImporter._parse_csv(csv)
    assert len(rows) == 1
    assert len(rows[0][1].authors) == 2


def test_parse_csv_two_separate_books():
    csv = (
        "title,published_year,genre_id,author_name,author_last_name,author_middle_name,author_pen_name\n"
        "Book A,2020,1,Alice,Smith,,\n"
        "Book B,2021,2,Bob,Jones,,\n"
    ).encode()
    rows, errors = BooksImporter._parse_csv(csv)
    assert len(rows) == 2
    assert len(errors) == 0
