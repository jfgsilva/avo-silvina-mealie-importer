import json
import logging
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Tuple

logger = logging.getLogger(__name__)


def iter_static(
    recipes_dir: Path, cuisine: Optional[str] = None
) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """Yield (cuisine, recipe_dict) pairs from recipes/**/*.json.

    If *cuisine* is given, only that subdirectory is walked.
    """
    if not recipes_dir.exists():
        logger.warning("Recipes directory not found: %s", recipes_dir)
        return

    if cuisine:
        dirs = [recipes_dir / cuisine]
    else:
        dirs = sorted(p for p in recipes_dir.iterdir() if p.is_dir())

    for cuisine_dir in dirs:
        if not cuisine_dir.exists():
            logger.warning("Cuisine directory not found: %s", cuisine_dir)
            continue

        for json_file in sorted(cuisine_dir.glob("*.json")):
            try:
                recipe = json.loads(json_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.error("Failed to load %s: %s", json_file, exc)
                continue

            yield cuisine_dir.name, recipe
