import logging
from pathlib import Path
from typing import Generator, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


def iter_urls(
    urls_dir: Path, cuisine: Optional[str] = None
) -> Generator[Tuple[str, str], None, None]:
    """Yield (cuisine, url) pairs from urls/*.yaml.

    If *cuisine* is given, only that cuisine's file is read.
    """
    if not urls_dir.exists():
        logger.warning("URLs directory not found: %s", urls_dir)
        return

    files = (
        [urls_dir / f"{cuisine}.yaml"] if cuisine else sorted(urls_dir.glob("*.yaml"))
    )

    for path in files:
        if not path.exists():
            logger.warning("URL file not found: %s", path)
            continue

        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            logger.error("Failed to parse %s: %s", path, exc)
            continue

        file_cuisine: str = data.get("cuisine", path.stem)
        for entry in data.get("recipes", []):
            if isinstance(entry, dict):
                url = entry.get("url", "")
            else:
                url = str(entry)
            if url:
                yield file_cuisine, url
