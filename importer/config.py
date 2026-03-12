import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    mealie_url: str
    mealie_token: str
    import_delay: float = 1.0
    urls_dir: Path = field(default_factory=lambda: Path("urls"))
    recipes_dir: Path = field(default_factory=lambda: Path("recipes"))


def load_config() -> Config:
    load_dotenv()

    url = os.environ.get("MEALIE_URL", "").rstrip("/")
    token = os.environ.get("MEALIE_TOKEN", "")

    missing = []
    if not url:
        missing.append("MEALIE_URL")
    if not token:
        missing.append("MEALIE_TOKEN")
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    delay = float(os.environ.get("IMPORT_DELAY_SECONDS", "1.0"))
    return Config(mealie_url=url, mealie_token=token, import_delay=delay)
