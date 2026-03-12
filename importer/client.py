import logging
from typing import Any, Optional, Set

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from importer.config import Config

logger = logging.getLogger(__name__)

_RETRY_STATUS = {429, 500, 502, 503, 504}


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, requests.HTTPError):
        return exc.response is not None and exc.response.status_code in _RETRY_STATUS
    return isinstance(exc, requests.ConnectionError)


class MealieClient:
    def __init__(self, config: Config, session: Optional[requests.Session] = None) -> None:
        self._base = config.mealie_url
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {config.mealie_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self._base}{path}"

    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        resp = self._session.request(method, self._url(path), timeout=30, **kwargs)
        resp.raise_for_status()
        return resp

    # ── public API ────────────────────────────────────────────────────────────

    def health_check(self) -> bool:
        """Return True if Mealie responds to a ping."""
        try:
            self._request("GET", "/api/app/about")
            return True
        except Exception:
            return False

    def get_existing_slugs(self) -> Set[str]:
        """Fetch all recipe slugs currently in Mealie."""
        resp = self._request("GET", "/api/recipes", params={"perPage": -1})
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        return {r["slug"] for r in items if "slug" in r}

    def import_from_url(self, url: str) -> str:
        """Ask Mealie to scrape a URL. Returns the new recipe slug."""
        resp = self._request(
            "POST",
            "/api/recipes/create/url",
            json={"url": url, "includeTags": False},
        )
        return resp.json()

    def import_from_json(self, recipe: "dict[str, Any]") -> str:
        """Create a recipe from a full JSON payload. Returns the new recipe slug."""
        # Step 1: create skeleton
        create_resp = self._request("POST", "/api/recipes", json={"name": recipe["name"]})
        slug: str = create_resp.json()

        # Step 2: patch with full data
        try:
            self._request("PATCH", f"/api/recipes/{slug}", json=recipe)
        except Exception as exc:
            logger.error("PATCH failed for slug %r, cleaning up skeleton: %s", slug, exc)
            try:
                self._session.delete(self._url(f"/api/recipes/{slug}"), timeout=10)
            except Exception:
                pass
            raise

        return slug

    def delete_recipe(self, slug: str) -> None:
        self._request("DELETE", f"/api/recipes/{slug}")
