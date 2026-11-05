"""Loading items and boxes from JSON files and saving results."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from binpacker.models import Box, Item


def _load_rows(path: str | Path, cls: type, kind: str) -> list:
    """Read a JSON list from path and build one cls per row, with readable errors."""
    try:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}") from None
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON in {path}: {e}") from e
    if not isinstance(rows, list):
        raise ValueError(f"top level must be a list ({kind} rows) in {path}")
    built = []
    for i, data in enumerate(rows):
        if not isinstance(data, dict):
            raise ValueError(f"{kind} row {i}: must be a JSON object")
        try:
            built.append(cls(**data))
        except (TypeError, ValueError) as e:
            raise ValueError(f"{kind} row {i}: {e}") from e
    return built


def load_boxes(path: str | Path) -> list[Box]:
    """Read a JSON list of boxes from a file."""
    return _load_rows(path, Box, "box")


def expand_quantity(item: Item) -> list[Item]:
    """Split an item with quantity N into N items named 'name#1'..'name#N'."""
    return [
        replace(item, name=f"{item.name}#{n}", quantity=1)
        for n in range(1, item.quantity + 1)
    ]


def load_items(path: str | Path) -> list[Item]:
    """Read a JSON list of items from a file, with quantity already expanded."""
    items = _load_rows(path, Item, "item")
    return [single for item in items for single in expand_quantity(item)]
