from openai import AsyncOpenAI

from App.Schemas.Book.BookResponse import BookResponse


class AiService:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    async def what_if(self, book: BookResponse) -> str:
        authors = ", ".join(" ".join(filter(None, [a.name, a.last_name])) for a in book.authors)
        prompt = (
            f'Generate a short "what if" alternative scenario (5-7 sentences) for the book '
            f'"{book.title}" ({book.published_year}) by {authors}, genre: {book.genre.name}. '
            f"Change a key plot point or ending in a surprising way. "
            f"Be creative, specific to this book, and make it different each time."
        )
        response = await self._client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=1.0,
        )
        return response.choices[0].message.content.strip()
