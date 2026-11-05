from __future__ import annotations

from pathlib import Path

from binpacker.geometry import validate_result
from binpacker.io import load_boxes, load_items
from binpacker.models import Box, Item, Placement
from binpacker.packer import _find_position, _fits, _sort_items, _update_points, pack

BOX = Box("B", 10, 10, 10)
ITEM = Item("x", 1, 1, 1)
FIRST = Placement(ITEM, 0, 0, 0, 2, 3, 4)
CORNERS = [(2, 0, 0), (0, 3, 0), (0, 0, 4)]
DATA = Path(__file__).resolve().parent.parent / "data"
ITEMS_FILE = DATA / "sample_items.json"
BOXES_FILE = DATA / "sample_boxes.json"


def _place(x, y, z, size=5):
    """Build a cubic Placement of the given size with its near corner at (x, y, z)."""
    return Placement(ITEM, x, y, z, size, size, size)


def test_sort_items_volume_descending_ties_by_name():
    """Biggest volume first; equal volumes are ordered by name."""
    items = [
        Item("b", 1, 1, 1),
        Item("big", 2, 2, 2),
        Item("a", 1, 1, 1),
        Item("mid", 1, 2, 2),
    ]
    assert [i.name for i in _sort_items(items)] == ["big", "mid", "a", "b"]


def test_fits_on_empty_list():
    """A placement inside the box fits when nothing is placed yet."""
    assert _fits(_place(0, 0, 0), [], BOX)


def test_fits_false_when_outside():
    """A placement sticking out of the box does not fit."""
    assert not _fits(_place(8, 0, 0), [], BOX)


def test_fits_false_when_overlapping():
    """A placement overlapping an already placed one does not fit."""
    assert not _fits(_place(3, 3, 3), [_place(0, 0, 0)], BOX)


def test_fits_true_when_only_touching():
    """A placement that only touches a placed one still fits."""
    assert _fits(_place(5, 0, 0), [_place(0, 0, 0)], BOX)


def test_find_position_empty_box_places_at_origin():
    """In an empty box the item goes to the first point, (0, 0, 0)."""
    p = _find_position(Item("a", 2, 2, 2), [], [(0, 0, 0)], BOX)
    assert p is not None
    assert (p.x, p.y, p.z) == (0, 0, 0)


def test_find_position_oversized_is_none():
    """An item bigger than the box in every orientation gets no position."""
    assert _find_position(Item("a", 11, 11, 11), [], [(0, 0, 0)], BOX) is None


def test_find_position_only_fits_rotated():
    """A long item fits only when rotated: None without rotation, placed with it."""
    tall = Box("T", 10, 2, 2)
    fixed = Item("a", 2, 2, 10, allow_rotation=False)
    free = Item("a", 2, 2, 10)
    assert _find_position(fixed, [], [(0, 0, 0)], tall) is None
    p = _find_position(free, [], [(0, 0, 0)], tall)
    assert p is not None
    assert (p.dx, p.dy, p.dz) == (10, 2, 2)


def test_update_points_after_one_item_gives_three_corners():
    """From the origin point, placing one item leaves exactly its 3 far corners."""
    assert _update_points([(0, 0, 0)], FIRST, [FIRST]) == sorted(CORNERS)


def test_update_points_removes_point_inside_item():
    """A point lying inside a placed item is removed."""
    result = _update_points([(0, 0, 0), (1, 1, 1)], FIRST, [FIRST])
    assert (1, 1, 1) not in result
    assert result == sorted(CORNERS)


def test_update_points_removes_duplicates():
    """A repeated point, or one equal to a new corner, appears only once."""
    result = _update_points([(2, 0, 0), (2, 0, 0), (0, 0, 0)], FIRST, [FIRST])
    assert len(result) == len(set(result))
    assert result == sorted(CORNERS)


def test_pack_eight_cubes_fill_box():
    """Eight 5x5x5 cubes fill a 10x10x10 box: 8 placed, 0 unpacked."""
    items = [Item(f"c{i}", 5, 5, 5) for i in range(8)]
    result = pack(items, BOX)
    assert len(result.placements) == 8
    assert result.unpacked == []


def test_pack_oversized_goes_to_unpacked():
    """An item bigger than the box is unpacked while a small one is placed."""
    ok = Item("ok", 2, 2, 2)
    big = Item("big", 11, 11, 11)
    result = pack([ok, big], BOX)
    assert [p.item.name for p in result.placements] == ["ok"]
    assert result.unpacked == [big]


def test_pack_presorted_keeps_given_order():
    """presorted=True places items in the given order; default sorts big first."""
    small = Item("small", 2, 2, 2)
    big = Item("big", 5, 5, 5)
    kept = pack([small, big], BOX, presorted=True)
    assert [p.item.name for p in kept.placements] == ["small", "big"]
    sorted_ = pack([small, big], BOX)
    assert [p.item.name for p in sorted_.placements] == ["big", "small"]


def test_pack_two_runs_give_equal_results():
    """Packing the same input twice gives equal results."""
    items = [
        Item("a", 4, 3, 2),
        Item("b", 5, 5, 5),
        Item("c", 2, 2, 2),
        Item("d", 3, 3, 3),
    ]
    assert pack(items, BOX) == pack(items, BOX)


def test_pack_weight_limit_allows_only_two_of_three():
    """A limit of 10 kg lets two 5 kg items in; the third goes to unpacked."""
    limited = Box("L", 10, 10, 10, max_weight=10)
    items = [Item(n, 2, 2, 2, weight=5) for n in "abc"]
    result = pack(items, limited)
    assert len(result.placements) == 2
    assert len(result.unpacked) == 1


def test_pack_infinite_limit_unaffected():
    """Without a weight limit, even very heavy items are all placed."""
    items = [Item(n, 2, 2, 2, weight=1000) for n in "abc"]
    result = pack(items, BOX)
    assert len(result.placements) == 3
    assert result.unpacked == []


def test_pack_weight_limited_result_is_valid():
    """A weight-limited result passes validate_result."""
    limited = Box("L", 10, 10, 10, max_weight=10)
    items = [Item(n, 2, 2, 2, weight=5) for n in "abc"]
    assert validate_result(pack(items, limited)) == []


def _sample_result():
    """Pack the sample items into the largest sample box; return (items, result)."""
    items = load_items(ITEMS_FILE)
    box = max(load_boxes(BOXES_FILE), key=lambda b: b.volume)
    return items, pack(items, box)


def test_sample_items_into_largest_box_is_valid():
    """Sample items packed into the largest sample box give a valid result."""
    _, result = _sample_result()
    assert validate_result(result) == []


def test_sample_every_item_appears_exactly_once():
    """Placed plus unpacked items are exactly the input items, each once."""
    items, result = _sample_result()
    seen = [p.item.name for p in result.placements] + [i.name for i in result.unpacked]
    assert sorted(seen) == sorted(i.name for i in items)


def test_pack_three_items_exact_positions():
    """Three fixed-orientation items land at hand-computed positions."""
    items = [
        Item("c", 10, 4, 3, allow_rotation=False),
        Item("a", 6, 6, 6, allow_rotation=False),
        Item("b", 4, 6, 6, allow_rotation=False),
    ]
    result = pack(items, BOX)
    got = [(p.item.name, p.x, p.y, p.z, p.dx, p.dy, p.dz) for p in result.placements]
    assert got == [
        ("a", 0, 0, 0, 6, 6, 6),
        ("b", 6, 0, 0, 4, 6, 6),
        ("c", 0, 6, 0, 10, 4, 3),
    ]
    assert result.unpacked == []


def test_sample_two_runs_are_equal():
    """Packing the sample twice gives equal results."""
    assert _sample_result()[1] == _sample_result()[1]
