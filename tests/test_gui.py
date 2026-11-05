import math

import pytest

from binpacker.gui import build_inputs
from binpacker.models import Box


def test_valid_rows_become_items_and_boxes():
    """Text rows are turned into an Item with the given size and weight and a Box with limit and cost."""
    items, boxes = build_inputs(
        [["Book", "20", "15", "3", "0.5", "1"]],
        [["Small", "30", "20", "10", "12", "1.5"]],
    )
    assert len(items) == 1
    book = items[0]
    assert book.name.startswith("Book")
    assert (book.length, book.width, book.height) == (20, 15, 3)
    assert book.weight == pytest.approx(0.5)
    assert boxes == [Box("Small", 30, 20, 10, max_weight=12, cost=1.5)]


def test_empty_optional_fields_use_defaults():
    """Empty weight -> 0, empty quantity -> 1, empty max_weight -> infinity, empty cost -> 0."""
    items, boxes = build_inputs([["Mug", "8", "8", "10", "", ""]], [["Crate", "40", "30", "20", "", ""]])
    assert len(items) == 1
    assert items[0].weight == 0
    assert items[0].quantity == 1
    assert boxes[0].max_weight == math.inf
    assert boxes[0].cost == 0


def test_bad_number_error_mentions_row_and_field():
    """A bad number raises ValueError naming the row (1-based) and the field, for items and for boxes."""
    good = ["Book", "20", "15", "3", "", ""]
    with pytest.raises(ValueError, match="item row 2.*width"):
        build_inputs([good, ["Mug", "8", "abc", "10", "", ""]], [])
    with pytest.raises(ValueError, match="box row 1.*max_weight"):
        build_inputs([], [["Big", "60", "40", "40", "heavy", ""]])


def test_quantity_expands_into_separate_items():
    """Quantity 3 gives three Items named Book#1..Book#3, each with quantity 1."""
    items, _ = build_inputs([["Book", "20", "15", "3", "0.5", "3"]], [])
    assert [i.name for i in items] == ["Book#1", "Book#2", "Book#3"]
    assert all(i.quantity == 1 for i in items)
