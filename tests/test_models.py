from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from binpacker.models import Box, Item, PackingResult, Placement


def _make(**overrides):
    """Build a valid Item, replacing the given fields."""
    values = {"name": "box", "length": 10, "width": 20, "height": 30}
    values.update(overrides)
    return Item(**values)


def _make_box(**overrides):
    """Build a valid Box, replacing the given fields."""
    values = {"name": "carton", "length": 100, "width": 50, "height": 40}
    values.update(overrides)
    return Box(**values)


def test_item_defaults():
    """Creating an Item with only the required fields uses the defaults."""
    item = Item("box", 10, 20, 30)
    assert item.name == "box"
    assert (item.length, item.width, item.height) == (10, 20, 30)
    assert item.weight == 0.0
    assert item.quantity == 1
    assert item.allow_rotation is True


def test_item_volume():
    """Volume is length * width * height."""
    assert Item("box", 10, 20, 30).volume == 6000


def test_item_is_frozen():
    """Assigning a field raises FrozenInstanceError."""
    item = Item("box", 10, 20, 30)
    with pytest.raises(FrozenInstanceError):
        item.length = 5


def test_item_valid_case():
    """A fully specified valid Item is accepted unchanged."""
    item = _make(weight=5.5, quantity=3, allow_rotation=False)
    assert (item.weight, item.quantity, item.allow_rotation) == (5.5, 3, False)


@pytest.mark.parametrize(
    "overrides, field",
    [
        pytest.param({"name": ""}, "name", id="empty-name"),
        pytest.param({"name": "   "}, "name", id="blank-name"),
        pytest.param({"length": 0}, "length", id="zero-length"),
        pytest.param({"width": 0}, "width", id="zero-width"),
        pytest.param({"height": -1}, "height", id="negative-height"),
        pytest.param({"weight": -0.5}, "weight", id="negative-weight"),
        pytest.param({"quantity": 0}, "quantity", id="zero-quantity"),
    ],
)
def test_item_invalid_values(overrides, field):
    """Each invalid value raises ValueError naming the bad field."""
    with pytest.raises(ValueError, match=field):
        _make(**overrides)


def test_box_valid_case():
    """A fully specified valid Box is accepted unchanged."""
    box = _make_box(max_weight=25.0, cost=3.5)
    assert (box.name, box.length, box.width, box.height) == ("carton", 100, 50, 40)
    assert (box.max_weight, box.cost) == (25.0, 3.5)


def test_box_volume():
    """Volume is length * width * height."""
    assert _make_box().volume == 200000


def test_box_default_max_weight_is_inf():
    """Without max_weight the limit is infinite and cost is 0."""
    box = _make_box()
    assert box.max_weight == float("inf")
    assert box.cost == 0.0


@pytest.mark.parametrize(
    "overrides, field",
    [
        pytest.param({"name": ""}, "name", id="empty-name"),
        pytest.param({"name": "   "}, "name", id="blank-name"),
        pytest.param({"length": 0}, "length", id="zero-length"),
        pytest.param({"width": 0}, "width", id="zero-width"),
        pytest.param({"height": -1}, "height", id="negative-height"),
        pytest.param({"max_weight": 0}, "max_weight", id="zero-max-weight"),
        pytest.param({"max_weight": -5}, "max_weight", id="negative-max-weight"),
        pytest.param({"cost": -0.5}, "cost", id="negative-cost"),
    ],
)
def test_box_invalid_values(overrides, field):
    """Each invalid value raises ValueError naming the bad field."""
    with pytest.raises(ValueError, match=field):
        _make_box(**overrides)


def _make_placement():
    """Item 10x20x30 placed at (1, 2, 3), turned to size 20x10x30."""
    return Placement(Item("box", 10, 20, 30), 1, 2, 3, 20, 10, 30)


def test_placement_far_corner():
    """x2, y2, z2 are the position plus the oriented size."""
    p = _make_placement()
    assert (p.x2, p.y2, p.z2) == (21, 12, 33)


def test_placement_volume():
    """Volume is dx * dy * dz."""
    assert _make_placement().volume == 6000


def test_packing_result_empty():
    """An empty result can be created with only a box."""
    result = PackingResult(_make_box())
    assert result.placements == []
    assert result.unpacked == []


def test_packing_result_lists_are_not_shared():
    """Two instances do not share the same lists."""
    a = PackingResult(_make_box())
    b = PackingResult(_make_box())
    a.placements.append(_make_placement())
    a.unpacked.append(Item("box", 10, 20, 30))
    assert b.placements == []
    assert b.unpacked == []
    assert a.placements is not b.placements
    assert a.unpacked is not b.unpacked
