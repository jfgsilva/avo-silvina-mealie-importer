# avo-silvina-mealie-importer

Bulk-import Portuguese and Mediterranean recipes into a self-hosted [Mealie](https://mealie.io) instance.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.tpl .env   # fill in MEALIE_URL and MEALIE_TOKEN
python -m importer --dry-run
```

## Usage

```bash
# Full import (URLs + static JSON)
python -m importer

# Single cuisine
python -m importer --cuisine portuguese

# Static JSON files only (no scraping)
python -m importer --source static

# URL scraping only
python -m importer --source urls

# Dry run — no writes to Mealie
python -m importer --dry-run

# Re-import even if the recipe already exists
python -m importer --no-skip-existing

# Import a single recipe from a URL
python -m importer --url https://example.com/recipe
```

## Docker / Podman

```bash
docker build -t mealie-importer .
docker run --env-file .env mealie-importer --dry-run

# Podman is identical
podman run --env-file .env mealie-importer
```

Or pull from GHCR:

```bash
docker run --env-file .env ghcr.io/jfsilva/avo-silvina-mealie-importer
```

## Configuration

Copy `.env.tpl` to `.env` and set:

| Variable | Required | Default | Description |
|---|---|---|---|
| `MEALIE_URL` | Yes | — | Base URL of your Mealie instance |
| `MEALIE_TOKEN` | Yes | — | Mealie API bearer token |
| `IMPORT_DELAY_SECONDS` | No | `1.0` | Delay between URL imports |

See `.env.tpl` for 1Password and Bitwarden injection examples.

## Sources

### Static JSON (`recipes/`)

Pre-curated recipes in Mealie's JSON format, ready to import without scraping.

```
recipes/
├── portuguese/   ← bacalhau_a_bras, caldo_verde, pasteis_de_nata …
└── mediterranean/ ← gazpacho, moussaka, shakshuka, tabbouleh …
```

### URLs (`urls/`)

YAML files listing public recipe URLs for Mealie's built-in scraper:

```yaml
cuisine: portuguese
recipes:
  - url: https://foodfromportugal.com/recipes/caldo-verde/
    note: "Classic kale soup"
```

## Development

```bash
pytest --cov=importer
```

## How URL scraping works

This tool does **not** scrape recipe sites itself. It delegates entirely to **Mealie's built-in scraper** via `POST /api/recipes/create/url`. Mealie uses [recipe-scrapers](https://github.com/hhursev/recipe-scrapers) under the hood, which supports 300+ sites including all the sites in `urls/`. The curated URL lists in this repo simply tell the importer which URLs to hand off to Mealie.
