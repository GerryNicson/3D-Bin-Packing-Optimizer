"""Matplotlib 3D drawing of a packing result."""
from __future__ import annotations

from itertools import combinations, product
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from binpacker.models import Box, PackingResult, Placement

_COLORS = [
    "tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple",
    "tab:brown", "tab:pink", "tab:gray", "tab:olive", "tab:cyan",
]


def _draw_box(ax: Axes, box: Box) -> None:
    """Draw the 12 edges of the box, from (0, 0, 0) to (L, W, H), on a 3D axes."""
    corners = product((0, box.length), (0, box.width), (0, box.height))
    for a, b in combinations(corners, 2):
        if sum(u != v for u, v in zip(a, b)) == 1:
            ax.plot(*zip(a, b), color="black")


def _draw_cuboid(ax: Axes, p: Placement, color: str) -> None:
    """Draw p as a translucent cuboid with its item name at the center."""
    x, y, z, x2, y2, z2 = p.x, p.y, p.z, p.x2, p.y2, p.z2
    faces = [
        [(x, y, z), (x2, y, z), (x2, y2, z), (x, y2, z)],
        [(x, y, z2), (x2, y, z2), (x2, y2, z2), (x, y2, z2)],
        [(x, y, z), (x2, y, z), (x2, y, z2), (x, y, z2)],
        [(x, y2, z), (x2, y2, z), (x2, y2, z2), (x, y2, z2)],
        [(x, y, z), (x, y2, z), (x, y2, z2), (x, y, z2)],
        [(x2, y, z), (x2, y2, z), (x2, y2, z2), (x2, y, z2)],
    ]
    solid = Poly3DCollection(faces, facecolors=to_rgba(color, 0.4), edgecolors="black")
    ax.add_collection3d(solid)
    ax.text((x + x2) / 2, (y + y2) / 2, (z + z2) / 2, p.item.name, ha="center", fontsize=8)


def make_figure(r: PackingResult, fig: Figure | None = None) -> Figure:
    """Draw the box and its placements on fig, or on a new Figure, and return it."""
    fig = Figure() if fig is None else fig
    ax = fig.add_subplot(projection="3d")
    box = r.box
    _draw_box(ax, box)
    for i, p in enumerate(r.placements):
        _draw_cuboid(ax, p, _COLORS[i % len(_COLORS)])
    ax.set_box_aspect((box.length, box.width, box.height))
    ax.set_xlabel("length (cm)")
    ax.set_ylabel("width (cm)")
    ax.set_zlabel("height (cm)")
    percent = 100 * sum(p.volume for p in r.placements) / box.volume
    ax.set_title(f"{box.name} - utilization {percent:.1f}%")
    return fig


def plot_result(r: PackingResult, path: str | Path | None = None, show: bool = False) -> None:
    """Build the figure, save a PNG if path is given, open a window if show is True."""
    if show:
        import matplotlib.pyplot as plt

        fig = make_figure(r, plt.figure())
    else:
        fig = make_figure(r)
    if path is not None:
        fig.savefig(path)
    if show:
        plt.show()
