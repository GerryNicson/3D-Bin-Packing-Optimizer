from __future__ import annotations

import json
from itertools import product

import pytest

from binpacker.metrics import report, save_result, total_weight, utilization, wasted_volume
from binpacker.models import Box, Item, PackingResult, Placement

BOX = Box("B", 10, 10, 10)


def _eight_cubes():
    """Build a result with eight 5x5x5 cubes filling the 10x10x10 box."""
    placements = [
        Placement(Item(f"c{i}", 5, 5, 5), x, y, z, 5, 5, 5)
        for i, (x, y, z) in enumerate(product((0, 5), repeat=3))
    ]
    return PackingResult(BOX, placements)


def test_eight_cubes_full_utilization_no_waste():
    """A completely filled box has utilization 1.0 and waste 0."""
    r = _eight_cubes()
    assert utilization(r) == pytest.approx(1.0)
    assert wasted_volume(r) == pytest.approx(0.0)


def test_empty_result_has_zero_utilization():
    """With nothing placed, utilization is 0.0 and all of the box is wasted."""
    r = PackingResult(BOX)
    assert utilization(r) == 0.0
    assert wasted_volume(r) == pytest.approx(1000.0)


def test_hand_calculated_fraction():
    """One 2x3x5 item (30) in a 1000 box: utilization 0.03, waste 970."""
    r = PackingResult(BOX, [Placement(Item("a", 2, 3, 5), 0, 0, 0, 2, 3, 5)])
    assert utilization(r) == pytest.approx(0.03)
    assert wasted_volume(r) == pytest.approx(970.0)


def test_total_weight_sums_packed_items_only():
    """Weights of placed items are added; unpacked items are ignored."""
    placements = [
        Placement(Item("a", 1, 1, 1, weight=1.5), 0, 0, 0, 1, 1, 1),
        Placement(Item("b", 1, 1, 1, weight=2.5), 1, 0, 0, 1, 1, 1),
        Placement(Item("c", 1, 1, 1, weight=4.0), 2, 0, 0, 1, 1, 1),
    ]
    r = PackingResult(BOX, placements, [Item("d", 1, 1, 1, weight=100.0)])
    assert total_weight(r) == pytest.approx(8.0)


def _report_text():
    """Report for two placed items (31 cm3 in a 1000 box) and two unpacked items."""
    box = Box("Crate", 10, 10, 10)
    placements = [
        Placement(Item("alpha", 2, 3, 5), 0, 0, 0, 2, 3, 5),
        Placement(Item("beta", 1, 1, 1), 2, 0, 0, 1, 1, 1),
    ]
    unpacked = [Item("gamma", 20, 20, 20), Item("delta", 30, 30, 30)]
    return report(PackingResult(box, placements, unpacked))


def test_report_contains_box_name_and_utilization_percent():
    """The report names the box and shows utilization as a percent (31/1000 = 3.1%)."""
    text = _report_text()
    assert "Crate" in text
    assert "3.1%" in text


def test_report_lists_every_placed_item():
    """Every placed item name appears in the report."""
    text = _report_text()
    assert "alpha" in text
    assert "beta" in text


def test_report_lists_unpacked_names():
    """The names of unpacked items are listed on the last line."""
    last = _report_text().splitlines()[-1]
    assert "gamma" in last
    assert "delta" in last


def test_save_result_roundtrip(tmp_path):
    """The saved JSON reloads with matching counts and values."""
    box = Box("Crate", 10, 10, 10)
    placements = [
        Placement(Item("alpha", 2, 3, 5, weight=1.5), 0, 0, 0, 2, 3, 5),
        Placement(Item("beta", 1, 1, 1, weight=2.0), 2, 0, 0, 1, 1, 1),
    ]
    r = PackingResult(box, placements, [Item("gamma", 20, 20, 20)])
    path = tmp_path / "result.json"
    save_result(r, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["box"]["name"] == "Crate"
    assert data["box"]["max_weight"] is None
    assert data["metrics"]["utilization"] == pytest.approx(0.031)
    assert data["metrics"]["wasted_volume"] == pytest.approx(969.0)
    assert data["metrics"]["total_weight"] == pytest.approx(3.5)
    assert len(data["placements"]) == 2
    first = {"name": "alpha", "x": 0, "y": 0, "z": 0, "dx": 2, "dy": 3, "dz": 5}
    assert data["placements"][0] == first
    assert data["unpacked"] == ["gamma"]
