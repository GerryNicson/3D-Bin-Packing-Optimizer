import re

import pytest

from binpacker import cli
from binpacker.cli import build_parser
from binpacker.costs import total_cost
from binpacker.models import Box, Item
from binpacker.packer import pack


def test_valid_args_parse_to_expected_values():
    """All options are read as given; --plot, --seed and --shipments fall back to their defaults."""
    args = build_parser().parse_args(
        ["pack", "--items", "items.csv", "--boxes", "boxes.csv", "--plot", "out.png", "--seed", "7", "--shipments", "12"]
    )
    assert args.command == "pack"
    assert args.items == "items.csv"
    assert args.boxes == "boxes.csv"
    assert args.plot == "out.png"
    assert args.seed == 7
    assert args.shipments == 12
    defaults = build_parser().parse_args(["pack", "--items", "i.csv", "--boxes", "b.csv"])
    assert defaults.plot is None
    assert defaults.seed == 0
    assert defaults.shipments == 1


def test_missing_items_raises_system_exit():
    """argparse exits when the required --items is left out."""
    with pytest.raises(SystemExit):
        build_parser().parse_args(["pack", "--boxes", "boxes.csv"])


def test_main_returns_zero_and_prints_report(monkeypatch, capsys):
    """main() returns 0 and prints a report containing 'Utilization' (loaders are stubbed, no files)."""
    monkeypatch.setattr(cli, "load_items", lambda path: [Item("a", 5, 5, 5), Item("b", 5, 5, 5)])
    monkeypatch.setattr(cli, "load_boxes", lambda path: [Box("Small", 10, 10, 10, cost=1.0)])
    code = cli.main(["pack", "--items", "items.csv", "--boxes", "boxes.csv"])
    assert code == 0
    assert "Utilization" in capsys.readouterr().out


def test_main_prints_savings_line_and_total_cost(monkeypatch, capsys):
    """The output has a savings line and a total cost equal to the sum of total_cost over the plan."""
    small = Box("Small", 10, 10, 10, cost=1.0)
    large = Box("Large", 40, 40, 40, cost=5.0)
    items = [Item("a", 5, 5, 5, weight=2.0), Item("b", 5, 5, 5, weight=2.0)]
    results = [pack(items, small)]
    assert results[0].unpacked == []
    monkeypatch.setattr(cli, "load_items", lambda path: items)
    monkeypatch.setattr(cli, "load_boxes", lambda path: [small, large])
    monkeypatch.setattr(cli, "select_box", lambda its, bxs, seed=0: results)
    code = cli.main(["pack", "--items", "items.csv", "--boxes", "boxes.csv", "--shipments", "10"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Savings" in out
    match = re.search(r"Total cost: ([0-9.]+)", out)
    assert match is not None
    assert float(match.group(1)) == pytest.approx(sum(total_cost(r) for r in results), abs=0.01)


def test_main_plot_saves_one_png_per_result(monkeypatch, tmp_path):
    """--plot writes out.png for one result, and plots_1.png and plots_2.png for two results."""
    small = Box("Small", 10, 10, 10, cost=1.0)
    first = [Item("a", 5, 5, 5)]
    second = [Item("b", 5, 5, 5)]
    single = [pack(first, small)]
    several = [pack(first, small), pack(second, small)]
    monkeypatch.setattr(cli, "load_items", lambda path: first + second)
    monkeypatch.setattr(cli, "load_boxes", lambda path: [small])
    monkeypatch.setattr(cli, "select_box", lambda its, bxs, seed=0: single)
    code = cli.main(["pack", "--items", "i.csv", "--boxes", "b.csv", "--plot", str(tmp_path / "out.png")])
    assert code == 0
    assert (tmp_path / "out.png").stat().st_size > 0
    monkeypatch.setattr(cli, "select_box", lambda its, bxs, seed=0: several)
    code = cli.main(["pack", "--items", "i.csv", "--boxes", "b.csv", "--plot", str(tmp_path / "plots.png")])
    assert code == 0
    assert (tmp_path / "plots_1.png").stat().st_size > 0
    assert (tmp_path / "plots_2.png").stat().st_size > 0
    assert not (tmp_path / "plots.png").exists()


def test_main_missing_items_file_returns_one_with_stderr_message(tmp_path, capsys):
    """A non-existent items file gives return code 1 and an error message on stderr."""
    code = cli.main(["pack", "--items", str(tmp_path / "missing.json"), "--boxes", str(tmp_path / "boxes.json")])
    captured = capsys.readouterr()
    assert code == 1
    assert "Error" in captured.err
