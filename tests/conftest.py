import json
from pathlib import Path

import pytest
import responses as responses_lib

FIXTURES = Path(__file__).parent / "fixtures"

SAMPLE_RECIPE = json.loads((FIXTURES / "sample_recipe.json").read_text())


@pytest.fixture
def mock_env(monkeypatch):
    """Inject valid Mealie environment variables."""
    monkeypatch.setenv("MEALIE_URL", "http://mealie.test")
    monkeypatch.setenv("MEALIE_TOKEN", "test-token-abc")
    monkeypatch.setenv("IMPORT_DELAY_SECONDS", "0")


@pytest.fixture
def mocked_responses():
    """Activate the `responses` HTTP-mocking library for the test."""
    with responses_lib.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps
