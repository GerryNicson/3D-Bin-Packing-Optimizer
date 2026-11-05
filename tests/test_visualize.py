from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from binpacker.models import Box, Item, PackingResult, Placement
from binpacker.visualize import _draw_box, _draw_cuboid, make_figure, plot_result


def test_draw_box_adds_twelve_edges():
    """Drawing a box adds exactly 12 lines to a 3D axes."""
    ax = Figure().add_subplot(projection="3d")
    _draw_box(ax, Box("B", 10, 6, 4))
    assert len(ax.lines) == 12


def test_draw_cuboid_adds_one_collection_and_one_text():
    """One cuboid adds 1 collection and 1 text label to the axes."""
    ax = Figure().add_subplot(projection="3d")
    collections, texts = len(ax.collections), len(ax.texts)
    _draw_cuboid(ax, Placement(Item("a", 2, 3, 4), 1, 1, 1, 2, 3, 4), "tab:blue")
    assert len(ax.collections) == collections + 1
    assert len(ax.texts) == texts + 1


def _result():
    """Two 5x5x5 items placed side by side in a 10x10x10 box."""
    placements = [
        Placement(Item("a", 5, 5, 5), 0, 0, 0, 5, 5, 5),
        Placement(Item("b", 5, 5, 5), 5, 0, 0, 5, 5, 5),
    ]
    return PackingResult(Box("B", 10, 10, 10), placements)


def test_plot_result_writes_nonempty_png(tmp_path):
    """plot_result with a path writes a PNG file that is not empty."""
    path = tmp_path / "out.png"
    plot_result(_result(), path=path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_make_figure_has_one_label_per_placement():
    """make_figure returns a Figure whose axes carry one text per placement."""
    fig = make_figure(_result())
    assert isinstance(fig, Figure)
    assert [t.get_text() for t in fig.axes[0].texts] == ["a", "b"]


def test_no_pyplot_figures_left_open(tmp_path):
    """Neither make_figure nor plot_result leaves a pyplot figure open."""
    make_figure(_result())
    plot_result(_result(), path=tmp_path / "out.png")
    assert plt.get_fignums() == []
