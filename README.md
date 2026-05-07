# Books API

A RESTful API for managing a book catalog built with FastAPI and PostgreSQL.

## Features

### Books
- Full CRUD — create, read, update, delete books
- Filter by title (partial match), genre, author name, publication year range
- Sorting by title, year, creation date, or author name
- Pagination with configurable limit and offset
- Multi-author support with full name fields (first name, last name, middle name, pen name)

### Authors
- Authors are automatically created or reused on book creation (get-or-create)
- Unique identity based on the combination of all name fields
- Shared across books — updating an author on one book does not affect others

### Genres
- Fixed lookup table seeded with 10 genres
- Validated on book create and update

### Authentication
- Registration and login return both access and refresh tokens
- Short-lived JWT access tokens (configurable, default 60 minutes)
- Opaque refresh tokens stored as SHA-256 hashes in the database
- Token rotation — each refresh invalidates the previous refresh token
- Logout endpoint revokes the refresh token

### Import / Export
- Bulk import from JSON or CSV via `POST /api/v1/books/import`
- JSON format: array of book objects matching the create schema
- CSV format: one row per author; rows with the same title + year + genre are grouped into one book with multiple authors
- Partial import — rows that fail validation or insertion are reported individually, valid rows are still imported
- Export to JSON or CSV via `GET /api/v1/books/export` with the same filters as the list endpoint

### Recommendations
- `GET /api/v1/books/{id}/recommendations` returns books scored by relevance
- +1 point for the same genre, +1 per shared author
- Books with score 0 are excluded

### AI — What If
- `GET /api/v1/books/{id}/what-if` generates a fresh alternative plot scenario for the book on every request
- Powered by OpenAI `gpt-4o-mini`
- Requires authentication
- Returns 503 if `OPENAI_API_KEY` is not configured — all other endpoints are unaffected

### Rate Limiting
- Global limit: 100 requests per minute per IP
- Stricter limit on auth endpoints: 5 requests per minute for `/auth/register` and `/auth/login`, 10 per minute for `/auth/refresh`

### Database Migrations
- Migrations run automatically on startup
- Applied migrations are tracked in the `_migrations` table
- Each migration runs in its own transaction — a failed migration does not affect previously applied ones

---

## API Documentation

Interactive documentation is available at the following URLs when the server is running:

| Interface | URL |
|-----------|-----|
| Swagger UI | http://localhost:8000/docs |
| Redoc | http://localhost:8000/redoc |

---

## Project Structure

```
App/
├── Api/V1/          — routers and dependencies
├── Config/          — settings loaded from environment
├── Db/              — connection pool, migration runner, SQL migration files
├── Repositories/    — raw SQL queries via asyncpg
├── Schemas/         — Pydantic request and response models
└── Services/        — business logic
Tests/
├── Unit/            — pure logic tests (JWT, CSV/JSON parser)
└── *.py             — integration tests using savepoint rollback
```

---

## Live Demo

The API is deployed on AWS EC2 and available at:

| Interface | URL |
|-----------|-----|
| Swagger UI | http://54.173.173.11:8000/docs |
| Redoc | http://54.173.173.11:8000/redoc |
| Base URL | http://54.173.173.11:8000 |

---

## Setup and Running Locally

### Requirements

- Docker
- Docker Compose

### 1. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set the required values:

```
JWT_SECRET=your-secret-key-at-least-32-characters
OPENAI_API_KEY=sk-...        # optional — only needed for /what-if endpoint
```

The remaining values can stay as-is for local development.

### 2. Start the services

```bash
docker compose up --build
```

This starts PostgreSQL and the API server. Database migrations run automatically on startup.

The API is available at http://localhost:8000.

### 3. Running tests

Tests run locally against the Docker PostgreSQL instance.

```bash
pip install -r requirements.txt
python -m pytest Tests/ -v
```

> The test suite uses savepoint-based rollback — each test wraps its DB operations in a transaction that is rolled back after the test, leaving the database clean.
