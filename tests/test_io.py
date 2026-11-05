from __future__ import annotations

import json
from pathlib import Path

import pytest

from binpacker.io import load_boxes, load_items
from binpacker.models import Box

DATA = Path(__file__).resolve().parent.parent / "data"

SAMPLE_ITEMS = [
    {"name": "box", "length": 30, "width": 20, "height": 10, "weight": 2.5, "quantity": 3},
    {"name": "tube", "length": 50, "width": 10, "height": 10, "weight": 1.0, "quantity": 2, "allow_rotation": False},
    {"name": "plate", "length": 40, "width": 40, "height": 2, "weight": 0.5, "quantity": 1},
]

GOOD_ROW = {"name": "ok", "length": 10, "width": 10, "height": 10}
LOADERS = [load_items, load_boxes]


def _write_items(tmp_path):
    """Write SAMPLE_ITEMS as a JSON file and return its path."""
    path = tmp_path / "items.json"
    path.write_text(json.dumps(SAMPLE_ITEMS), encoding="utf-8")
    return path


def _write_text(tmp_path, text):
    """Write raw text to a JSON file and return its path."""
    path = tmp_path / "data.json"
    path.write_text(text, encoding="utf-8")
    return path


def test_load_boxes_sample():
    """sample_boxes.json gives 3 Boxes with the expected first values."""
    boxes = load_boxes(DATA / "sample_boxes.json")
    assert len(boxes) == 3
    assert all(isinstance(b, Box) for b in boxes)
    assert boxes[0] == Box("Small", 30, 20, 20, max_weight=8.0, cost=2.0)


def test_load_items_sample(tmp_path):
    """A sample items file loads with the first item expanded to name#1."""
    items = load_items(_write_items(tmp_path))
    assert items
    first = items[0]
    assert (first.name, first.length, first.width, first.height) == ("box#1", 30, 20, 10)
    assert first.quantity == 1


def test_load_items_count_equals_sum_of_quantities(tmp_path):
    """Loaded item count equals the sum of all quantities."""
    items = load_items(_write_items(tmp_path))
    assert len(items) == sum(d["quantity"] for d in SAMPLE_ITEMS)


def test_load_items_names_unique(tmp_path):
    """All loaded item names are unique."""
    names = [item.name for item in load_items(_write_items(tmp_path))]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("loader", LOADERS)
def test_error_file_not_found(tmp_path, loader):
    """A missing file raises a readable ValueError."""
    with pytest.raises(ValueError, match="file not found"):
        loader(tmp_path / "missing.json")


@pytest.mark.parametrize("loader", LOADERS)
def test_error_invalid_json(tmp_path, loader):
    """Broken JSON raises a readable ValueError."""
    with pytest.raises(ValueError, match="invalid JSON"):
        loader(_write_text(tmp_path, "{oops"))


@pytest.mark.parametrize("loader", LOADERS)
def test_error_top_level_not_a_list(tmp_path, loader):
    """A JSON object at the top level raises a readable ValueError."""
    with pytest.raises(ValueError, match="top level must be a list"):
        loader(_write_text(tmp_path, json.dumps({"name": "x"})))


@pytest.mark.parametrize("loader", LOADERS)
def test_error_missing_field_mentions_row(tmp_path, loader):
    """A row without required fields raises a ValueError naming that row."""
    rows = [GOOD_ROW, {"name": "bad"}]
    with pytest.raises(ValueError, match=r"row 1:"):
        loader(_write_text(tmp_path, json.dumps(rows)))


@pytest.mark.parametrize("loader", LOADERS)
def test_error_invalid_value_mentions_row(tmp_path, loader):
    """A row with an invalid value raises a ValueError naming that row."""
    rows = [GOOD_ROW, GOOD_ROW, {**GOOD_ROW, "length": -5}]
    with pytest.raises(ValueError, match=r"row 2:"):
        loader(_write_text(tmp_path, json.dumps(rows)))
