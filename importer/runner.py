import logging
import time
from typing import Any, Dict, Optional, Set

from importer.client import MealieClient
from importer.config import Config
from importer.sources.static_source import iter_static
from importer.sources.url_source import iter_urls

logger = logging.getLogger(__name__)


class Runner:
    def __init__(self, config: Config, dry_run: bool = False, skip_existing: bool = True) -> None:
        self._config = config
        self._dry_run = dry_run
        self._skip_existing = skip_existing
        self._client = MealieClient(config)

    def run(self, cuisine: Optional[str] = None, source: str = "all") -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%H:%M:%S",
        )

        if self._dry_run:
            logger.info("DRY RUN — no writes will be made to Mealie.")

        existing: Set[str] = set()
        if self._skip_existing and not self._dry_run:
            logger.info("Fetching existing recipe slugs from Mealie…")
            existing = self._client.get_existing_slugs()
            logger.info("Found %d existing recipes.", len(existing))

        stats = {"imported": 0, "skipped": 0, "failed": 0}

        if source in ("all", "urls"):
            self._run_urls(cuisine, existing, stats)

        if source in ("all", "static"):
            self._run_static(cuisine, existing, stats)

        logger.info(
            "Done. imported=%d  skipped=%d  failed=%d",
            stats["imported"],
            stats["skipped"],
            stats["failed"],
        )

    def run_single_url(self, url: str) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%H:%M:%S",
        )
        if self._dry_run:
            logger.info("DRY RUN — would import %s", url)
            return
        try:
            slug = self._client.import_from_url(url)
            logger.info("OK   %s → %s", url, slug)
        except Exception as exc:
            logger.warning("FAIL %s: %s", url, exc)

    # ── URL import ────────────────────────────────────────────────────────────

    def _run_urls(
        self, cuisine: Optional[str], existing: Set[str], stats: Dict[str, int]
    ) -> None:
        for recipe_cuisine, url in iter_urls(self._config.urls_dir, cuisine):
            if self._skip_existing and self._url_already_imported(url, existing):
                logger.info("SKIP (url known)  %s", url)
                stats["skipped"] += 1
                continue

            if self._dry_run:
                logger.info("DRY  [%s] %s", recipe_cuisine, url)
                stats["imported"] += 1
                continue

            try:
                slug = self._client.import_from_url(url)
                logger.info("OK   [%s] %s → %s", recipe_cuisine, url, slug)
                existing.add(slug)
                stats["imported"] += 1
            except Exception as exc:
                logger.warning("FAIL [%s] %s: %s", recipe_cuisine, url, exc)
                stats["failed"] += 1

            time.sleep(self._config.import_delay)

    def _url_already_imported(self, url: str, existing_slugs: Set[str]) -> bool:
        # Mealie slug is derived from the recipe title, not the URL, so we
        # cannot cheaply check by slug here.  A proper check would need the
        # full recipe list with orgURL — for now, always return False so we
        # rely on Mealie's own deduplication on the server side.
        return False

    # ── Static JSON import ────────────────────────────────────────────────────

    def _run_static(
        self, cuisine: Optional[str], existing: Set[str], stats: Dict[str, int]
    ) -> None:
        for recipe_cuisine, recipe in iter_static(self._config.recipes_dir, cuisine):
            name: str = recipe.get("name", "<unknown>")
            slug_candidate = _slugify(name)

            if self._skip_existing and slug_candidate in existing:
                logger.info("SKIP (exists) %r", name)
                stats["skipped"] += 1
                continue

            if self._dry_run:
                logger.info("DRY  [%s] %r", recipe_cuisine, name)
                stats["imported"] += 1
                continue

            try:
                slug = self._client.import_from_json(recipe)
                logger.info("OK   [%s] %r → %s", recipe_cuisine, name, slug)
                existing.add(slug)
                stats["imported"] += 1
            except Exception as exc:
                logger.warning("FAIL [%s] %r: %s", recipe_cuisine, name, exc)
                stats["failed"] += 1


def _slugify(name: str) -> str:
    """Very rough slug approximation matching Mealie's behaviour."""
    import re

    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
