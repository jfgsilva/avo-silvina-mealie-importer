import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from importer.config import Config
from importer.runner import Runner


@pytest.fixture
def config(tmp_path):
    urls_dir = tmp_path / "urls"
    urls_dir.mkdir()
    recipes_dir = tmp_path / "recipes"
    recipes_dir.mkdir()

    (urls_dir / "portuguese.yaml").write_text(
        "cuisine: portuguese\nrecipes:\n  - url: https://example.com/r1\n"
    )

    portuguese_dir = recipes_dir / "portuguese"
    portuguese_dir.mkdir()
    (portuguese_dir / "soup.json").write_text(
        json.dumps({"name": "Caldo Verde", "recipeIngredient": []})
    )

    return Config(
        mealie_url="http://mealie.test",
        mealie_token="tok",
        import_delay=0,
        urls_dir=urls_dir,
        recipes_dir=recipes_dir,
    )


def test_dry_run_no_http_writes(config):
    with patch("importer.runner.MealieClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.get_existing_slugs.return_value = set()

        runner = Runner(config=config, dry_run=True, skip_existing=False)
        runner.run(source="all")

        # No import calls should have been made
        mock_client.import_from_url.assert_not_called()
        mock_client.import_from_json.assert_not_called()


def test_skip_existing_static(config):
    with patch("importer.runner.MealieClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.get_existing_slugs.return_value = {"caldo-verde"}

        runner = Runner(config=config, dry_run=False, skip_existing=True)
        runner.run(source="static")

        mock_client.import_from_json.assert_not_called()


def test_static_import_called(config):
    with patch("importer.runner.MealieClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.get_existing_slugs.return_value = set()
        mock_client.import_from_json.return_value = "caldo-verde"

        runner = Runner(config=config, dry_run=False, skip_existing=True)
        runner.run(source="static")

        mock_client.import_from_json.assert_called_once()


def test_url_import_called(config):
    with patch("importer.runner.MealieClient") as MockClient, \
         patch("importer.runner._fetch_og_image", return_value=""):
        mock_client = MockClient.return_value
        mock_client.get_existing_slugs.return_value = set()
        mock_client.import_from_url.return_value = "new-slug"

        runner = Runner(config=config, dry_run=False, skip_existing=True)
        runner.run(source="urls")

        mock_client.import_from_url.assert_called_once_with("https://example.com/r1")


def test_url_import_uploads_image(config):
    """After a successful URL import, image should be fetched via og:image of the source URL."""
    with patch("importer.runner.MealieClient") as MockClient, \
         patch("importer.runner._fetch_og_image", return_value="https://example.com/img.jpg") as mock_fetch:
        mock_client = MockClient.return_value
        mock_client.get_existing_slugs.return_value = set()
        mock_client.import_from_url.return_value = "new-slug"

        runner = Runner(config=config, dry_run=False, skip_existing=False)
        runner.run(source="urls")

        mock_fetch.assert_called_once_with("https://example.com/r1")
        mock_client.upload_image_from_url.assert_called_once_with(
            "new-slug", "https://example.com/img.jpg"
        )


def test_failed_import_does_not_abort(config):
    """A single import failure should not stop the rest of the run."""
    with patch("importer.runner.MealieClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.get_existing_slugs.return_value = set()
        mock_client.import_from_json.side_effect = Exception("Mealie error")

        # Add a second recipe so we can verify the run continues
        portuguese_dir = config.recipes_dir / "portuguese"
        (portuguese_dir / "second.json").write_text(
            json.dumps({"name": "Second Dish", "recipeIngredient": []})
        )
        mock_client.import_from_json.side_effect = [Exception("error"), "second-dish"]

        runner = Runner(config=config, dry_run=False, skip_existing=False)
        runner.run(source="static")  # should not raise

        assert mock_client.import_from_json.call_count == 2


def test_static_import_uploads_image_from_org_url(config):
    """After a successful static import, image should be uploaded from og:image of orgURL."""
    portuguese_dir = config.recipes_dir / "portuguese"
    (portuguese_dir / "soup.json").write_text(
        json.dumps({"name": "Caldo Verde", "recipeIngredient": [], "orgURL": "https://example.com/page"})
    )

    with patch("importer.runner.MealieClient") as MockClient, \
         patch("importer.runner._fetch_og_image", return_value="https://example.com/img.jpg") as mock_fetch:
        mock_client = MockClient.return_value
        mock_client.get_existing_slugs.return_value = set()
        mock_client.import_from_json.return_value = "caldo-verde"

        runner = Runner(config=config, dry_run=False, skip_existing=False)
        runner.run(source="static")

        mock_fetch.assert_called_once_with("https://example.com/page")
        mock_client.upload_image_from_url.assert_called_once_with(
            "caldo-verde", "https://example.com/img.jpg"
        )


def test_static_import_image_upload_failure_does_not_abort(config):
    """A failed image upload should not count as an import failure."""
    with patch("importer.runner.MealieClient") as MockClient, \
         patch("importer.runner._fetch_og_image", return_value="https://example.com/img.jpg"):
        mock_client = MockClient.return_value
        mock_client.get_existing_slugs.return_value = set()
        mock_client.import_from_json.return_value = "caldo-verde"
        mock_client.upload_image_from_url.side_effect = Exception("upload failed")

        runner = Runner(config=config, dry_run=False, skip_existing=False)
        runner.run(source="static")  # should not raise

        mock_client.import_from_json.assert_called_once()


def test_static_import_no_image_when_no_org_url(config):
    """No image upload attempt when recipe has neither image nor orgURL."""
    with patch("importer.runner.MealieClient") as MockClient, \
         patch("importer.runner._fetch_og_image", return_value="") as mock_fetch:
        mock_client = MockClient.return_value
        mock_client.get_existing_slugs.return_value = set()
        mock_client.import_from_json.return_value = "caldo-verde"

        runner = Runner(config=config, dry_run=False, skip_existing=False)
        runner.run(source="static")

        mock_client.upload_image_from_url.assert_not_called()


def test_static_import_image_from_explicit_image_field(config):
    """Explicit 'image' field in JSON takes priority over orgURL scraping."""
    portuguese_dir = config.recipes_dir / "portuguese"
    (portuguese_dir / "soup.json").write_text(
        json.dumps({
            "name": "Caldo Verde",
            "recipeIngredient": [],
            "image": "https://example.com/explicit.jpg",
            "orgURL": "https://example.com/page",
        })
    )

    with patch("importer.runner.MealieClient") as MockClient, \
         patch("importer.runner._fetch_og_image") as mock_fetch:
        mock_client = MockClient.return_value
        mock_client.get_existing_slugs.return_value = set()
        mock_client.import_from_json.return_value = "caldo-verde"

        runner = Runner(config=config, dry_run=False, skip_existing=False)
        runner.run(source="static")

        mock_fetch.assert_not_called()
        mock_client.upload_image_from_url.assert_called_once_with(
            "caldo-verde", "https://example.com/explicit.jpg"
        )


def test_cuisine_filter(config):
    """--cuisine should restrict both URL and static sources."""
    # Add mediterranean URL source
    (config.urls_dir / "mediterranean.yaml").write_text(
        "cuisine: mediterranean\nrecipes:\n  - url: https://example.com/med\n"
    )

    with patch("importer.runner.MealieClient") as MockClient, \
         patch("importer.runner._fetch_og_image", return_value=""):
        mock_client = MockClient.return_value
        mock_client.get_existing_slugs.return_value = set()
        mock_client.import_from_url.return_value = "slug"

        runner = Runner(config=config, dry_run=False, skip_existing=False)
        runner.run(source="urls", cuisine="mediterranean")

        calls = [c.args[0] for c in mock_client.import_from_url.call_args_list]
        assert all("med" in url for url in calls)
