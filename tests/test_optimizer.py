from pathlib import Path

from binpacker.geometry import validate_result
from binpacker.io import load_boxes, load_items
from binpacker.models import Box, Item
from binpacker.optimizer import STRATEGIES, _score, _strategy_orders, best_pack, select_box
from binpacker.packer import pack

DATA = Path(__file__).resolve().parent.parent / "data"

# Hand-made set. Weight tie between C and D tests the name tie-break.
ITEMS = [
    Item("A", 10, 10, 10, weight=1.0),  # volume 1000, longest 10, height 10
    Item("B", 30, 2, 2, weight=5.0),    # volume 120,  longest 30, height 2
    Item("C", 5, 5, 20, weight=3.0),    # volume 500,  longest 20, height 20
    Item("D", 8, 8, 8, weight=3.0),     # volume 512,  longest 8,  height 8
]

EXPECTED = {
    "volume": ["A", "D", "C", "B"],
    "longest_side": ["B", "C", "A", "D"],
    "height": ["C", "A", "D", "B"],
    "weight": ["B", "C", "D", "A"],
}

SMALL = Box("Small", 10, 10, 10, cost=1.0)
MEDIUM = Box("Medium", 20, 20, 20, cost=2.0)
LARGE = Box("Large", 40, 40, 40, cost=5.0)
BOXES = [LARGE, SMALL, MEDIUM]  # unsorted on purpose


def _sample():
    """Load the sample items and sample boxes."""
    return load_items(DATA / "sample_items.json"), load_boxes(DATA / "sample_boxes.json")


def _strategies_only(items, box):
    """Best result over the strategy orders alone (the step 32 behaviour)."""
    results = [pack(order, box, presorted=True) for order in _strategy_orders(items)]
    return max(results, key=_score)


def _assert_each_item_once(items, results):
    """Placed items plus the last unpacked equal the input; leftovers are handed on exactly."""
    placed = sum(len(r.placements) for r in results)
    assert placed + len(results[-1].unpacked) == len(items)
    for prev, nxt in zip(results, results[1:]):
        assert len(prev.unpacked) == len(nxt.placements) + len(nxt.unpacked)


def test_four_orders_returned():
    """One order per strategy, four in total, each holding every item."""
    orders = _strategy_orders(ITEMS)
    assert len(orders) == 4
    assert len(STRATEGIES) == 4
    for order in orders:
        assert sorted(i.name for i in order) == ["A", "B", "C", "D"]


def test_each_order_sorted_descending_on_hand_made_set():
    """Each strategy order is sorted descending by its key (tie: name)."""
    orders = _strategy_orders(ITEMS)
    for name, order in zip(STRATEGIES, orders):
        assert [i.name for i in order] == EXPECTED[name], name


def test_best_pack_score_never_lower_than_plain_pack():
    """On every sample box, best_pack scores at least as high as plain pack()."""
    items, boxes = _sample()
    for box in boxes:
        assert _score(best_pack(items, box)) >= _score(pack(items, box))


def test_best_pack_result_passes_validate_result():
    """On every sample box, the best_pack result has no validation errors."""
    items, boxes = _sample()
    for box in boxes:
        assert validate_result(best_pack(items, box)) == []


def test_same_seed_gives_equal_placements():
    """Two runs with the same seed give equal results on every sample box."""
    items, boxes = _sample()
    for box in boxes:
        assert best_pack(items, box, seed=7) == best_pack(items, box, seed=7)


def test_zero_restarts_equals_strategies_only():
    """restarts=0 returns exactly the strategies-only result."""
    items, boxes = _sample()
    for box in boxes:
        assert best_pack(items, box, restarts=0) == _strategies_only(items, box)


def test_restarts_never_worse_than_strategies_only():
    """Random restarts never score lower than the strategies-only result."""
    items, boxes = _sample()
    for box in boxes:
        with_restarts = best_pack(items, box, seed=3, restarts=20)
        assert _score(with_restarts) >= _score(_strategies_only(items, box))


def test_result_with_restarts_is_valid():
    """The result with random restarts passes validate_result on every sample box."""
    items, boxes = _sample()
    for box in boxes:
        assert validate_result(best_pack(items, box, seed=3, restarts=20)) == []


def test_select_box_small_set_gets_cheapest_box():
    """A tiny item fits every box, so the cheapest box is chosen."""
    results = select_box([Item("cube", 5, 5, 5)], BOXES)
    assert len(results) == 1
    assert results[0].box == SMALL
    assert results[0].unpacked == []


def test_select_box_set_needing_bigger_box_gets_that_box():
    """Three 10 cm cubes do not all fit the small box, so the medium box is chosen."""
    items = [Item(n, 10, 10, 10) for n in ("a", "b", "c")]
    results = select_box(items, BOXES)
    assert len(results) == 1
    assert results[0].box == MEDIUM
    assert results[0].unpacked == []


def test_select_box_too_many_items_gives_several_valid_results():
    """Three 30 cm cubes (one per large box) give 2+ valid results, each item once."""
    items = [Item(n, 30, 30, 30) for n in ("x", "y", "z")]
    results = select_box(items, BOXES)
    assert len(results) >= 2
    for r in results:
        assert validate_result(r) == []
    _assert_each_item_once(items, results)
    assert results[-1].unpacked == []


def test_select_box_impossible_item_stays_in_last_unpacked():
    """An item bigger than every box is left in the last result's unpacked."""
    items = [Item("x", 30, 30, 30), Item("y", 30, 30, 30), Item("huge", 50, 50, 50)]
    results = select_box(items, BOXES)
    assert len(results) == 2
    _assert_each_item_once(items, results)
    last = results[-1].unpacked
    assert len(last) == 1
    assert (last[0].length, last[0].width, last[0].height) == (50, 50, 50)


def test_select_box_all_impossible_gives_one_result_without_placements():
    """When no item fits any box there is one result with 0 placements."""
    items = [Item("h1", 50, 50, 50), Item("h2", 50, 50, 50)]
    results = select_box(items, BOXES)
    assert len(results) == 1
    assert results[0].placements == []
    assert len(results[0].unpacked) == 2
