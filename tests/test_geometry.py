from __future__ import annotations

from binpacker.geometry import inside, orientations, overlaps, validate_result
from binpacker.models import Box, Item, PackingResult, Placement

ITEM = Item("a", 1, 1, 1)
BOX = Box("B", 10, 20, 30)


def _place(x, y, z, size=10):
    """Build a cubic Placement of the given size with its near corner at (x, y, z)."""
    return Placement(ITEM, x, y, z, size, size, size)


def _fit(x, y, z, dx=10, dy=20, dz=30):
    """Build a Placement with the given corner and oriented size (default fills BOX)."""
    return Placement(ITEM, x, y, z, dx, dy, dz)


def _named(name, x, y, z, size=5):
    """Build a cubic Placement of an item with the given name."""
    return Placement(Item(name, 1, 1, 1), x, y, z, size, size, size)


def _heavy(name, x, weight):
    """Build a size-5 Placement at (x, 0, 0) for an item with the given weight."""
    return Placement(Item(name, 1, 1, 1, weight=weight), x, 0, 0, 5, 5, 5)


def test_normal_item_has_six_orientations():
    """Three different sides give 6 unique orientations."""
    result = orientations(Item("a", 1, 2, 3))
    assert len(result) == 6
    assert len(set(result)) == 6


def test_cube_has_one_orientation():
    """A cube gives a single orientation."""
    assert orientations(Item("a", 2, 2, 2)) == [(2, 2, 2)]


def test_two_equal_sides_have_three_orientations():
    """Two equal sides give 3 unique orientations."""
    result = orientations(Item("a", 2, 2, 3))
    assert len(result) == 3
    assert len(set(result)) == 3


def test_no_rotation_has_one_orientation():
    """allow_rotation=False keeps only (length, width, height)."""
    assert orientations(Item("a", 1, 2, 3, allow_rotation=False)) == [(1, 2, 3)]


def test_overlaps_touching_is_false():
    """Boxes sharing a face or an edge do not overlap."""
    base = _place(0, 0, 0)
    assert not overlaps(base, _place(10, 0, 0))
    assert not overlaps(_place(10, 0, 0), base)
    assert not overlaps(base, _place(10, 10, 0))


def test_overlaps_partial_is_true():
    """Boxes that share only part of their volume overlap."""
    assert overlaps(_place(0, 0, 0), _place(5, 5, 5))
    assert overlaps(_place(5, 5, 5), _place(0, 0, 0))


def test_overlaps_one_inside_another_is_true():
    """A small box fully inside a big one overlaps it."""
    big, small = _place(0, 0, 0), _place(2, 2, 2, size=3)
    assert overlaps(big, small)
    assert overlaps(small, big)


def test_overlaps_identical_is_true():
    """Two boxes at the same position and size overlap."""
    assert overlaps(_place(0, 0, 0), _place(0, 0, 0))


def test_overlaps_far_apart_is_false():
    """Boxes with a gap between them do not overlap."""
    assert not overlaps(_place(0, 0, 0), _place(50, 50, 50))


def test_inside_exactly_fills_box_is_true():
    """A placement that exactly fills the box is inside."""
    assert inside(_fit(0, 0, 0), BOX)


def test_inside_sticking_out_is_false():
    """Sticking out past the box on any one axis is not inside."""
    assert not inside(_fit(1, 0, 0), BOX)
    assert not inside(_fit(0, 1, 0), BOX)
    assert not inside(_fit(0, 0, 1), BOX)


def test_inside_negative_coordinate_is_false():
    """A negative coordinate on any axis is not inside."""
    assert not inside(_fit(-1, 0, 0, 5, 5, 5), BOX)
    assert not inside(_fit(0, -1, 0, 5, 5, 5), BOX)
    assert not inside(_fit(0, 0, -1, 5, 5, 5), BOX)


def test_validate_valid_result_is_empty():
    """Two separate placements inside the box give no messages."""
    result = PackingResult(BOX, [_named("alpha", 0, 0, 0), _named("beta", 5, 0, 0)])
    assert validate_result(result) == []


def test_validate_detects_outside():
    """A placement sticking out of the box is reported by item name."""
    result = PackingResult(BOX, [_named("alpha", 0, 0, 0), _named("beta", 8, 0, 0)])
    errors = validate_result(result)
    assert len(errors) == 1
    assert "beta" in errors[0]
    assert "alpha" not in errors[0]


def test_validate_detects_overlap():
    """Two overlapping placements are reported with both item names."""
    result = PackingResult(BOX, [_named("alpha", 0, 0, 0), _named("beta", 3, 3, 3)])
    errors = validate_result(result)
    assert len(errors) == 1
    assert "alpha" in errors[0]
    assert "beta" in errors[0]


def test_validate_under_weight_limit_is_empty():
    """Total weight under max_weight gives no messages."""
    box = Box("B", 10, 10, 10, max_weight=10.0)
    result = PackingResult(box, [_heavy("alpha", 0, 4.0), _heavy("beta", 5, 4.0)])
    assert validate_result(result) == []


def test_validate_over_weight_limit_gives_message():
    """Total weight above max_weight gives one weight message."""
    box = Box("B", 10, 10, 10, max_weight=10.0)
    result = PackingResult(box, [_heavy("alpha", 0, 6.0), _heavy("beta", 5, 6.0)])
    errors = validate_result(result)
    assert len(errors) == 1
    assert "weight" in errors[0]


def test_validate_infinite_weight_limit_is_empty():
    """A box without a weight limit accepts any total weight."""
    box = Box("B", 10, 10, 10)
    result = PackingResult(box, [_heavy("alpha", 0, 1e9), _heavy("beta", 5, 1e9)])
    assert validate_result(result) == []
