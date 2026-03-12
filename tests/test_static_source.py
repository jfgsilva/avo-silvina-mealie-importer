import json
from pathlib import Path

import pytest

from importer.sources.static_source import iter_static


def _write_recipe(path: Path, name: str) -> None:
    path.write_text(json.dumps({"name": name, "recipeIngredient": []}))


def test_iter_static_normal(tmp_path):
    cuisine_dir = tmp_path / "portuguese"
    cuisine_dir.mkdir()
    _write_recipe(cuisine_dir / "soup.json", "Caldo Verde")
    _write_recipe(cuisine_dir / "cod.json", "Bacalhau")

    results = list(iter_static(tmp_path))
    names = [r["name"] for _, r in results]
    assert "Caldo Verde" in names
    assert "Bacalhau" in names
    assert all(c == "portuguese" for c, _ in results)


def test_iter_static_cuisine_filter(tmp_path):
    for c in ("portuguese", "mediterranean"):
        d = tmp_path / c
        d.mkdir()
        _write_recipe(d / "recipe.json", f"Recipe from {c}")

    results = list(iter_static(tmp_path, cuisine="portuguese"))
    assert len(results) == 1
    assert results[0][0] == "portuguese"


def test_iter_static_missing_dir():
    results = list(iter_static(Path("/nonexistent/dir")))
    assert results == []


def test_iter_static_missing_cuisine_dir(tmp_path):
    results = list(iter_static(tmp_path, cuisine="doesnotexist"))
    assert results == []


def test_iter_static_invalid_json(tmp_path):
    cuisine_dir = tmp_path / "test"
    cuisine_dir.mkdir()
    (cuisine_dir / "bad.json").write_text("{ invalid json }")
    # Should skip the bad file and not raise
    results = list(iter_static(tmp_path))
    assert results == []


def test_iter_static_skips_non_json_files(tmp_path):
    cuisine_dir = tmp_path / "portuguese"
    cuisine_dir.mkdir()
    _write_recipe(cuisine_dir / "real.json", "Real Recipe")
    (cuisine_dir / "readme.txt").write_text("ignore me")

    results = list(iter_static(tmp_path))
    assert len(results) == 1
