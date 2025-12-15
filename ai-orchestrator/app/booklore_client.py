import httpx
from .settings import settings

class BookloreClient:
    def __init__(self) -> None:
        self.base = settings.booklore_base_url.rstrip("/")
        self.token = settings.booklore_api_token

    def _headers(self) -> dict:
        h = {"accept": "application/json"}
        if self.token:
            h["authorization"] = f"Bearer {self.token}"
        return h

    async def list_books(self, limit: int = 50, offset: int = 0) -> dict:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{self.base}/api/books",
                headers=self._headers(),
                params={"limit": limit, "offset": offset},
            )
            r.raise_for_status()
            return r.json()

    async def set_book_tags(self, book_id: str | int, tags: list[str]) -> dict:
        payload = {"tags": tags}
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.patch(
                f"{self.base}/api/books/{book_id}",
                headers={**self._headers(), "content-type": "application/json"},
                json=payload,
            )
            r.raise_for_status()
            return r.json()
