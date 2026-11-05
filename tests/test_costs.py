import pytest

from binpacker.costs import dimensional_weight, naive_plan, savings, shipping_cost, total_cost
from binpacker.geometry import validate_result
from binpacker.models import Box, Item
from binpacker.packer import pack

SMALL = Box("Small", 10, 10, 10, cost=1.0)
MEDIUM = Box("Medium", 20, 20, 20, cost=2.0)
LARGE = Box("Large", 40, 40, 40, cost=5.0)
BOXES = [MEDIUM, LARGE, SMALL]  # unsorted on purpose


def test_dimensional_weight_wins():
    """Light items in a big box: 50*40*25/5000 = 10 kg beats 5 kg actual; 10 * 1.5 = 15."""
    box = Box("Big", 50, 40, 25)
    items = [Item("a", 10, 10, 10, weight=2.0), Item("b", 10, 10, 10, weight=3.0)]
    r = pack(items, box)
    assert r.unpacked == []
    assert dimensional_weight(box) == pytest.approx(10.0)
    assert shipping_cost(r, rate_per_kg=1.5) == pytest.approx(15.0)


def test_actual_weight_wins():
    """Heavy items in a small box: 10 kg actual beats 20*20*20/4000 = 2 kg; 10 * 2 = 20."""
    box = Box("Small", 20, 20, 20)
    items = [Item("a", 5, 5, 5, weight=4.0), Item("b", 5, 5, 5, weight=6.0)]
    r = pack(items, box)
    assert r.unpacked == []
    assert dimensional_weight(box, divisor=4000) == pytest.approx(2.0)
    assert shipping_cost(r, rate_per_kg=2.0, divisor=4000) == pytest.approx(20.0)


def test_total_cost_is_box_cost_plus_shipping():
    """Box cost 3 + shipping (10 kg dimensional * 1.5 = 15) = 18."""
    box = Box("Crate", 50, 40, 25, cost=3.0)
    items = [Item("a", 10, 10, 10, weight=2.0), Item("b", 10, 10, 10, weight=3.0)]
    r = pack(items, box)
    assert r.unpacked == []
    assert total_cost(r, rate_per_kg=1.5) == pytest.approx(18.0)


def test_naive_plan_fits_in_one_box_gives_one_result():
    """A tiny item still goes into the largest box (baseline), in a single result."""
    results = naive_plan([Item("cube", 5, 5, 5)], BOXES)
    assert len(results) == 1
    assert results[0].box == LARGE
    assert results[0].unpacked == []


def test_naive_plan_too_many_items_gives_several_valid_results():
    """Three 30 cm cubes (one per large box) give 2+ valid results holding all three."""
    items = [Item(n, 30, 30, 30) for n in ("x", "y", "z")]
    results = naive_plan(items, BOXES)
    assert len(results) >= 2
    for r in results:
        assert r.box == LARGE
        assert validate_result(r) == []
    assert sum(len(r.placements) for r in results) == 3
    assert results[-1].unpacked == []


def test_naive_plan_impossible_item_is_reported_unpacked():
    """An item bigger than every box ends up in the last result's unpacked."""
    items = [Item("x", 30, 30, 30), Item("huge", 50, 50, 50)]
    results = naive_plan(items, BOXES)
    assert len(results) == 1
    last = results[-1].unpacked
    assert len(last) == 1
    assert (last[0].length, last[0].width, last[0].height) == (50, 50, 50)


def _item(name):
    """A 5 cm cube weighing 2 kg."""
    return Item(name, 5, 5, 5, weight=2.0)


def _packed(items, box):
    """Pack items into one box and check that everything fit."""
    r = pack(items, box)
    assert r.unpacked == []
    return r


def test_savings_hand_calculated():
    """Two Small boxes (2 * (1 + 2 kg * 1.5) = 8) vs one Crate (5 + 10 kg * 1.5 = 20), 10 a month."""
    crate = Box("Crate", 50, 40, 25, cost=5.0)
    optimized = [_packed([_item("a")], SMALL), _packed([_item("b")], SMALL)]
    naive = [_packed([_item("a"), _item("b")], crate)]
    out = savings(optimized, naive, shipments_per_month=10, rate_per_kg=1.5)
    assert out["optimized_cost"] == pytest.approx(8.0)
    assert out["naive_cost"] == pytest.approx(20.0)
    assert out["saving_per_shipment"] == pytest.approx(12.0)
    assert out["saving_per_month"] == pytest.approx(120.0)
    assert out["saving_pct"] == pytest.approx(60.0)


def test_savings_zero_when_plans_are_equal():
    """The same plan on both sides: cost 1 + 2 kg * 1.5 = 4, nothing saved."""
    plan = [_packed([_item("a")], SMALL)]
    out = savings(plan, plan, shipments_per_month=5, rate_per_kg=1.5)
    assert out["optimized_cost"] == pytest.approx(4.0)
    assert out["naive_cost"] == pytest.approx(4.0)
    assert out["saving_per_shipment"] == pytest.approx(0.0)
    assert out["saving_per_month"] == pytest.approx(0.0)
    assert out["saving_pct"] == pytest.approx(0.0)


def test_savings_no_division_by_zero_when_naive_cost_is_zero():
    """An empty naive plan costs 0, so saving_pct is 0 instead of a ZeroDivisionError."""
    plan = [_packed([_item("a")], SMALL)]
    out = savings(plan, [])
    assert out["naive_cost"] == pytest.approx(0.0)
    assert out["saving_pct"] == pytest.approx(0.0)
    empty = savings([], [], shipments_per_month=10)
    assert empty["saving_per_month"] == pytest.approx(0.0)
    assert empty["saving_pct"] == pytest.approx(0.0)
