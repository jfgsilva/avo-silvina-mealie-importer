from pathlib import Path

import pytest

from importer.sources.url_source import iter_urls

FIXTURES = Path(__file__).parent / "fixtures"


def test_iter_urls_normal(tmp_path):
    yaml_file = tmp_path / "portuguese.yaml"
    yaml_file.write_text(
        "cuisine: portuguese\nrecipes:\n  - url: https://a.com/r1\n  - url: https://b.com/r2\n"
    )
    results = list(iter_urls(tmp_path))
    assert results == [("portuguese", "https://a.com/r1"), ("portuguese", "https://b.com/r2")]


def test_iter_urls_cuisine_filter(tmp_path):
    (tmp_path / "portuguese.yaml").write_text(
        "cuisine: portuguese\nrecipes:\n  - url: https://a.com/r1\n"
    )
    (tmp_path / "mediterranean.yaml").write_text(
        "cuisine: mediterranean\nrecipes:\n  - url: https://b.com/r2\n"
    )
    results = list(iter_urls(tmp_path, cuisine="portuguese"))
    assert all(c == "portuguese" for c, _ in results)
    assert len(results) == 1


def test_iter_urls_empty_recipes(tmp_path):
    (tmp_path / "empty.yaml").write_text("cuisine: test\nrecipes: []\n")
    assert list(iter_urls(tmp_path)) == []


def test_iter_urls_missing_dir():
    results = list(iter_urls(Path("/nonexistent/path")))
    assert results == []


def test_iter_urls_missing_cuisine_file(tmp_path):
    results = list(iter_urls(tmp_path, cuisine="nonexistent"))
    assert results == []


def test_iter_urls_dict_entries_with_notes(tmp_path):
    (tmp_path / "test.yaml").write_text(
        "cuisine: test\nrecipes:\n  - url: https://c.com/r1\n    note: 'some note'\n"
    )
    results = list(iter_urls(tmp_path))
    assert results == [("test", "https://c.com/r1")]


def test_iter_urls_uses_filename_as_cuisine_fallback(tmp_path):
    (tmp_path / "myfile.yaml").write_text("recipes:\n  - url: https://x.com/\n")
    results = list(iter_urls(tmp_path))
    assert results[0][0] == "myfile"
