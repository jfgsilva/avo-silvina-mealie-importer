import json

import pytest
import responses as responses_lib

from importer.client import MealieClient
from importer.config import Config

BASE = "http://mealie.test"


@pytest.fixture
def config():
    return Config(mealie_url=BASE, mealie_token="tok", import_delay=0)


@pytest.fixture
def client(config):
    return MealieClient(config)


# ── health_check ──────────────────────────────────────────────────────────────

@responses_lib.activate
def test_health_check_ok(client):
    responses_lib.add(responses_lib.GET, f"{BASE}/api/app/about", json={"version": "1.0"})
    assert client.health_check() is True


@responses_lib.activate
def test_health_check_fail(client):
    responses_lib.add(responses_lib.GET, f"{BASE}/api/app/about", status=500)
    assert client.health_check() is False


# ── get_existing_slugs ────────────────────────────────────────────────────────

@responses_lib.activate
def test_get_existing_slugs(client):
    responses_lib.add(
        responses_lib.GET,
        f"{BASE}/api/recipes",
        json={"items": [{"slug": "caldo-verde"}, {"slug": "gazpacho"}]},
    )
    slugs = client.get_existing_slugs()
    assert slugs == {"caldo-verde", "gazpacho"}


@responses_lib.activate
def test_get_existing_slugs_empty(client):
    responses_lib.add(responses_lib.GET, f"{BASE}/api/recipes", json={"items": []})
    assert client.get_existing_slugs() == set()


# ── import_from_url ───────────────────────────────────────────────────────────

@responses_lib.activate
def test_import_from_url_returns_slug(client):
    responses_lib.add(
        responses_lib.POST,
        f"{BASE}/api/recipes/create/url",
        json="new-recipe-slug",
        status=201,
    )
    slug = client.import_from_url("https://example.com/recipe")
    assert slug == "new-recipe-slug"

    req = responses_lib.calls[0].request
    body = json.loads(req.body)
    assert body["url"] == "https://example.com/recipe"
    assert body["includeTags"] is False


@responses_lib.activate
def test_import_from_url_raises_on_4xx(client):
    responses_lib.add(
        responses_lib.POST, f"{BASE}/api/recipes/create/url", status=422
    )
    import requests
    with pytest.raises(requests.HTTPError):
        client.import_from_url("https://bad.example.com/")


# ── import_from_json ──────────────────────────────────────────────────────────

@responses_lib.activate
def test_import_from_json_success(client):
    responses_lib.add(
        responses_lib.POST, f"{BASE}/api/recipes", json="test-soup", status=201
    )
    responses_lib.add(
        responses_lib.PATCH,
        f"{BASE}/api/recipes/test-soup",
        json={"slug": "test-soup"},
        status=200,
    )

    from tests.conftest import SAMPLE_RECIPE
    slug = client.import_from_json(SAMPLE_RECIPE)
    assert slug == "test-soup"


@responses_lib.activate
def test_import_from_json_patch_failure_cleans_up(client):
    """When PATCH fails, the skeleton should be deleted."""
    responses_lib.add(
        responses_lib.POST, f"{BASE}/api/recipes", json="orphan-slug", status=201
    )
    responses_lib.add(
        responses_lib.PATCH, f"{BASE}/api/recipes/orphan-slug", status=500
    )
    responses_lib.add(
        responses_lib.DELETE, f"{BASE}/api/recipes/orphan-slug", status=200
    )

    import requests
    from tests.conftest import SAMPLE_RECIPE
    with pytest.raises(requests.HTTPError):
        client.import_from_json(SAMPLE_RECIPE)

    # DELETE should have been called
    methods = [c.request.method for c in responses_lib.calls]
    assert "DELETE" in methods
