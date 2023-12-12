import asyncio
import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from brave.client import BraveAPIClient
from brave.exceptions import BraveError
from brave.types import WebSearchApiResponse
import os
from typing import Optional, Dict

# Your API key for Brave
api_key = "yourapi"

class AsyncBrave(BraveAPIClient):
    """Asynchronous client for interacting with the Brave Search API."""

    def __init__(self, api_key: Optional[str] = None, endpoint: str = "web") -> None:
        super().__init__(api_key=api_key, endpoint=endpoint)

    async def _get(self, params: Dict = None) -> httpx.Response:
        """
        Perform an asynchronous GET request to the specified endpoint with optional parameters.
        Includes retry logic using tenacity.
        """
        url = self.base_url + self.endpoint + "/search"
        headers = self._prepare_headers()

        async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_fixed(2)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()  # Raises HTTPError for bad requests
                    return response

    async def search(
        self, q: str, country: Optional[str] = "GB", search_lang: Optional[str] = None, ui_lang: Optional[str] = None, 
        count: int = 3, offset: Optional[int] = 3, safesearch: Optional[str] = "off", 
        freshness: Optional[str] = "pw", text_decorations: Optional[bool] = True, spellcheck: Optional[bool] = True, 
        result_filter: Optional[str] = None, goggles_id: Optional[str] = None, units: Optional[str] = None, 
        extra_snippets: Optional[bool] = False,
    ) -> WebSearchApiResponse:
        """
        Perform a search using the Brave Search API.
        """
        # Parameter validation and query parameter construction
        if not q or len(q) > 400 or len(q.split()) > 50:
            raise ValueError("Invalid query parameter 'q'")

        params = {
            "q": q,
            "country": "GB",
            "search_lang": search_lang,
            "ui_lang": ui_lang,
            "count": min(count, 3),
            "offset": min(offset, 3),
            "safesearch": "off",
            "freshness": "off",
            "text_decorations": text_decorations,
            "spellcheck": spellcheck,
            "result_filter": result_filter,
            "goggles_id": goggles_id,
            "units": units,
            "extra_snippets": extra_snippets,
        }

        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # API request and response handling
        response = await self._get(params=params)

        # Error handling and data parsing
        if response.status_code != 200:
            raise BraveError(f"API Error: {response.status_code} - {response.text}")

        return WebSearchApiResponse.model_validate(response.json())

# Main function
async def main():
    # Create an instance of the AsyncBrave client with your API key
    brave = AsyncBrave(api_key=api_key)

    # Perform a Brave search
    search_results = await brave.search(q="question")

    # Extract URLs from the search results and print them
    urls = [str(result.url) for result in search_results.web.results]
    for url in urls:
        print(url)

# Execute the main function
if __name__ == "__main__":
    asyncio.run(main())
