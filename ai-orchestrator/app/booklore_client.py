"""
BookLore API client for the AI Orchestrator.

Provides async methods for interacting with the BookLore backend API,
including books, shelves, and magic shelves management.
"""

from dataclasses import dataclass
from enum import Enum

import httpx

from .settings import settings


class IconType(str, Enum):
    """Icon type enum matching backend IconType."""
    PRIME_NG = "PRIME_NG"


class BookloreAPIError(Exception):
    """Exception raised when BookLore API returns an error."""

    def __init__(self, status_code: int, message: str, response_body: str | None = None):
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"BookLore API error ({status_code}): {message}")


@dataclass
class Shelf:
    """Shelf data structure."""
    id: int
    name: str
    icon: str
    icon_type: str
    user_id: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Shelf":
        return cls(
            id=data["id"],
            name=data["name"],
            icon=data["icon"],
            icon_type=data.get("iconType", "PRIME_NG"),
            user_id=data.get("userId"),
        )


@dataclass
class MagicShelf:
    """Magic shelf data structure."""
    id: int | None
    name: str
    icon: str
    icon_type: str
    filter_json: str
    is_public: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "MagicShelf":
        return cls(
            id=data.get("id"),
            name=data["name"],
            icon=data["icon"],
            icon_type=data.get("iconType", "PRIME_NG"),
            filter_json=data["filterJson"],
            is_public=data.get("isPublic", False),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "iconType": self.icon_type,
            "filterJson": self.filter_json,
            "isPublic": self.is_public,
        }


class BookloreClient:
    """
    Async client for the BookLore API.

    Provides methods for managing books, shelves, and magic shelves.
    """

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        """
        Initialize the BookLore client.

        Args:
            base_url: BookLore API base URL. Defaults to settings.booklore_base_url.
            token: API authentication token. Defaults to settings.booklore_api_token.
        """
        self.base = (base_url or settings.booklore_base_url).rstrip("/")
        self.token = token or settings.booklore_api_token
        self.timeout = 30.0

    def _headers(self) -> dict:
        """Build request headers with authentication."""
        headers = {"accept": "application/json"}
        if self.token:
            headers["authorization"] = f"Bearer {self.token}"
        return headers

    def _json_headers(self) -> dict:
        """Build request headers for JSON requests."""
        return {**self._headers(), "content-type": "application/json"}

    async def _handle_response(self, response: httpx.Response) -> dict | list | None:
        """Handle API response and raise appropriate errors."""
        if response.status_code >= 400:
            try:
                body = response.text
            except Exception:
                body = None
            raise BookloreAPIError(
                status_code=response.status_code,
                message=response.reason_phrase or "Unknown error",
                response_body=body,
            )

        if response.status_code == 204:
            return None

        return response.json()

    # =========================================================================
    # Books API
    # =========================================================================

    async def list_books(
        self,
        limit: int = 50,
        offset: int = 0,
        library_id: int | None = None,
    ) -> dict:
        """
        List books with pagination.

        Args:
            limit: Maximum number of books to return.
            offset: Number of books to skip.
            library_id: Optional library ID to filter by.

        Returns:
            Dictionary with books data.
        """
        params = {"limit": limit, "offset": offset}
        if library_id:
            params["libraryId"] = library_id

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base}/api/books",
                headers=self._headers(),
                params=params,
            )
            return await self._handle_response(response)

    async def get_book(self, book_id: int) -> dict:
        """
        Get a single book by ID.

        Args:
            book_id: The book ID.

        Returns:
            Book data dictionary.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base}/api/books/{book_id}",
                headers=self._headers(),
            )
            return await self._handle_response(response)

    async def get_all_books_with_metadata(self, batch_size: int = 100) -> list[dict]:
        """
        Get all books with their metadata.

        Fetches books in batches to handle large libraries.

        Args:
            batch_size: Number of books to fetch per request.

        Returns:
            List of all books with metadata.
        """
        all_books = []
        offset = 0

        while True:
            result = await self.list_books(limit=batch_size, offset=offset)
            books = result.get("items", result) if isinstance(result, dict) else result

            if not books:
                break

            all_books.extend(books)
            offset += batch_size

            # If we got fewer books than requested, we've reached the end
            if len(books) < batch_size:
                break

        return all_books

    async def search_books(self, query: str, limit: int = 50) -> list[dict]:
        """
        Search books by text query.

        Args:
            query: Search text (matches title, author, description, etc.).
            limit: Maximum number of results.

        Returns:
            List of matching books.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base}/api/books/search",
                headers=self._headers(),
                params={"q": query, "limit": limit},
            )
            return await self._handle_response(response)

    async def set_book_tags(self, book_id: int, tags: list[str]) -> dict:
        """
        Set tags for a book.

        Args:
            book_id: The book ID.
            tags: List of tag names.

        Returns:
            Updated book data.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base}/api/books/{book_id}",
                headers=self._json_headers(),
                json={"tags": tags},
            )
            return await self._handle_response(response)

    # =========================================================================
    # Shelves API
    # =========================================================================

    async def get_shelves(self) -> list[Shelf]:
        """
        Get all shelves for the current user.

        Returns:
            List of Shelf objects.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base}/api/v1/shelves",
                headers=self._headers(),
            )
            data = await self._handle_response(response)
            return [Shelf.from_dict(s) for s in data]

    async def get_shelf(self, shelf_id: int) -> Shelf:
        """
        Get a shelf by ID.

        Args:
            shelf_id: The shelf ID.

        Returns:
            Shelf object.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base}/api/v1/shelves/{shelf_id}",
                headers=self._headers(),
            )
            data = await self._handle_response(response)
            return Shelf.from_dict(data)

    async def create_shelf(
        self,
        name: str,
        icon: str = "pi pi-bookmark",
        icon_type: str = "PRIME_NG",
    ) -> Shelf:
        """
        Create a new shelf.

        Args:
            name: Shelf name.
            icon: PrimeNG icon class (e.g., "pi pi-bookmark").
            icon_type: Icon type, defaults to "PRIME_NG".

        Returns:
            Created Shelf object.
        """
        payload = {
            "name": name,
            "icon": icon,
            "iconType": icon_type,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base}/api/v1/shelves",
                headers=self._json_headers(),
                json=payload,
            )
            data = await self._handle_response(response)
            return Shelf.from_dict(data)

    async def update_shelf(
        self,
        shelf_id: int,
        name: str | None = None,
        icon: str | None = None,
        icon_type: str | None = None,
    ) -> Shelf:
        """
        Update an existing shelf.

        Args:
            shelf_id: The shelf ID to update.
            name: New shelf name (optional).
            icon: New icon class (optional).
            icon_type: New icon type (optional).

        Returns:
            Updated Shelf object.
        """
        # First get current shelf to preserve unchanged fields
        current = await self.get_shelf(shelf_id)

        payload = {
            "name": name or current.name,
            "icon": icon or current.icon,
            "iconType": icon_type or current.icon_type,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(
                f"{self.base}/api/v1/shelves/{shelf_id}",
                headers=self._json_headers(),
                json=payload,
            )
            data = await self._handle_response(response)
            return Shelf.from_dict(data)

    async def delete_shelf(self, shelf_id: int) -> None:
        """
        Delete a shelf.

        Args:
            shelf_id: The shelf ID to delete.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base}/api/v1/shelves/{shelf_id}",
                headers=self._headers(),
            )
            await self._handle_response(response)

    async def get_shelf_books(self, shelf_id: int) -> list[dict]:
        """
        Get all books on a shelf.

        Args:
            shelf_id: The shelf ID.

        Returns:
            List of books on the shelf.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base}/api/v1/shelves/{shelf_id}/books",
                headers=self._headers(),
            )
            return await self._handle_response(response)

    async def assign_books_to_shelves(
        self,
        book_ids: list[int],
        shelves_to_assign: list[int] | None = None,
        shelves_to_unassign: list[int] | None = None,
    ) -> list[dict]:
        """
        Assign or unassign books to/from shelves.

        Args:
            book_ids: List of book IDs to modify.
            shelves_to_assign: List of shelf IDs to add books to.
            shelves_to_unassign: List of shelf IDs to remove books from.

        Returns:
            List of updated books.
        """
        payload = {
            "bookIds": book_ids,
            "shelvesToAssign": shelves_to_assign or [],
            "shelvesToUnassign": shelves_to_unassign or [],
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base}/api/v1/books/shelves",
                headers=self._json_headers(),
                json=payload,
            )
            return await self._handle_response(response)

    # =========================================================================
    # Magic Shelves API
    # =========================================================================

    async def get_magic_shelves(self) -> list[MagicShelf]:
        """
        Get all magic shelves for the current user.

        Returns:
            List of MagicShelf objects.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base}/api/magic-shelves",
                headers=self._headers(),
            )
            data = await self._handle_response(response)
            return [MagicShelf.from_dict(s) for s in data]

    async def get_magic_shelf(self, shelf_id: int) -> MagicShelf:
        """
        Get a magic shelf by ID.

        Args:
            shelf_id: The magic shelf ID.

        Returns:
            MagicShelf object.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base}/api/magic-shelves/{shelf_id}",
                headers=self._headers(),
            )
            data = await self._handle_response(response)
            return MagicShelf.from_dict(data)

    async def create_magic_shelf(
        self,
        name: str,
        filter_json: str,
        icon: str = "pi pi-sparkles",
        icon_type: str = "PRIME_NG",
        is_public: bool = False,
    ) -> MagicShelf:
        """
        Create a new magic shelf.

        Args:
            name: Shelf name.
            filter_json: JSON string with filter rules.
            icon: PrimeNG icon class.
            icon_type: Icon type.
            is_public: Whether the shelf is public.

        Returns:
            Created MagicShelf object.
        """
        shelf = MagicShelf(
            id=None,
            name=name,
            icon=icon,
            icon_type=icon_type,
            filter_json=filter_json,
            is_public=is_public,
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base}/api/magic-shelves",
                headers=self._json_headers(),
                json=shelf.to_dict(),
            )
            data = await self._handle_response(response)
            return MagicShelf.from_dict(data)

    async def update_magic_shelf(self, shelf: MagicShelf) -> MagicShelf:
        """
        Update an existing magic shelf.

        Args:
            shelf: MagicShelf object with updated data (must have id set).

        Returns:
            Updated MagicShelf object.
        """
        if shelf.id is None:
            raise ValueError("MagicShelf must have an id to update")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base}/api/magic-shelves",
                headers=self._json_headers(),
                json=shelf.to_dict(),
            )
            data = await self._handle_response(response)
            return MagicShelf.from_dict(data)

    async def delete_magic_shelf(self, shelf_id: int) -> None:
        """
        Delete a magic shelf.

        Args:
            shelf_id: The magic shelf ID to delete.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base}/api/magic-shelves/{shelf_id}",
                headers=self._headers(),
            )
            await self._handle_response(response)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def find_shelf_by_name(self, name: str) -> Shelf | None:
        """
        Find a shelf by name.

        Args:
            name: Shelf name to search for (case-insensitive).

        Returns:
            Shelf if found, None otherwise.
        """
        shelves = await self.get_shelves()
        name_lower = name.lower()
        for shelf in shelves:
            if shelf.name.lower() == name_lower:
                return shelf
        return None

    async def find_or_create_shelf(
        self,
        name: str,
        icon: str = "pi pi-bookmark",
        icon_type: str = "PRIME_NG",
    ) -> Shelf:
        """
        Find a shelf by name or create it if it doesn't exist.

        Args:
            name: Shelf name.
            icon: Icon class for new shelf.
            icon_type: Icon type for new shelf.

        Returns:
            Existing or newly created Shelf.
        """
        existing = await self.find_shelf_by_name(name)
        if existing:
            return existing
        return await self.create_shelf(name, icon, icon_type)

    async def get_books_by_category(self, category: str) -> list[dict]:
        """
        Get books that have a specific category.

        Args:
            category: Category name to filter by.

        Returns:
            List of books with the specified category.
        """
        all_books = await self.get_all_books_with_metadata()
        category_lower = category.lower()

        matching_books = []
        for book in all_books:
            metadata = book.get("metadata", {})
            categories = metadata.get("categories", [])
            # Categories can be strings or objects with name field
            for cat in categories:
                cat_name = cat.get("name", cat) if isinstance(cat, dict) else cat
                if category_lower in cat_name.lower():
                    matching_books.append(book)
                    break

        return matching_books

    async def get_books_by_author(self, author: str) -> list[dict]:
        """
        Get books by a specific author.

        Args:
            author: Author name to filter by (partial match).

        Returns:
            List of books by the author.
        """
        all_books = await self.get_all_books_with_metadata()
        author_lower = author.lower()

        matching_books = []
        for book in all_books:
            metadata = book.get("metadata", {})
            authors = metadata.get("authors", [])
            for auth in authors:
                auth_name = auth.get("name", auth) if isinstance(auth, dict) else auth
                if author_lower in auth_name.lower():
                    matching_books.append(book)
                    break

        return matching_books
