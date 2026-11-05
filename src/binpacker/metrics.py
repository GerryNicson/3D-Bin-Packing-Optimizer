"""Basic metrics for a packing result."""
from __future__ import annotations

import json
from pathlib import Path

from binpacker.models import PackingResult


def _used_volume(r: PackingResult) -> float:
    """Return the summed volume of all placements."""
    return float(sum(p.volume for p in r.placements))


def utilization(r: PackingResult) -> float:
    """Return used volume / box volume, between 0 and 1."""
    return _used_volume(r) / r.box.volume


def wasted_volume(r: PackingResult) -> float:
    """Return box volume minus used volume."""
    return r.box.volume - _used_volume(r)


def total_weight(r: PackingResult) -> float:
    """Return the sum of the weights of all packed items."""
    return float(sum(p.item.weight for p in r.placements))


def report(r: PackingResult) -> str:
    """Return a multi-line text report of the packing result."""
    box = r.box
    limit = "no limit" if box.max_weight == float("inf") else f"{box.max_weight:g} kg"
    lines = [
        f"Box: {box.name} ({box.length:g} x {box.width:g} x {box.height:g} cm)",
        f"Packed: {len(r.placements)}, unpacked: {len(r.unpacked)}",
        f"Utilization: {utilization(r) * 100:.1f}%",
        f"Wasted volume: {wasted_volume(r):.1f} cm3",
        f"Weight: {total_weight(r):g} kg / {limit}",
        "Placements:",
    ]
    for p in r.placements:
        pos = f"({p.x:g}, {p.y:g}, {p.z:g})"
        lines.append(f"  {p.item.name}: at {pos}, size {p.dx:g} x {p.dy:g} x {p.dz:g}")
    lines.append("Unpacked: " + (", ".join(i.name for i in r.unpacked) or "none"))
    return "\n".join(lines)


def save_result(r: PackingResult, path: str | Path) -> None:
    """Write the box, metrics, placements and unpacked names to a JSON file."""
    box = r.box
    data = {
        "box": {
            "name": box.name,
            "length": box.length,
            "width": box.width,
            "height": box.height,
            "max_weight": None if box.max_weight == float("inf") else box.max_weight,
            "cost": box.cost,
        },
        "metrics": {
            "utilization": utilization(r),
            "wasted_volume": wasted_volume(r),
            "total_weight": total_weight(r),
        },
        "placements": [
            {
                "name": p.item.name,
                "x": p.x,
                "y": p.y,
                "z": p.z,
                "dx": p.dx,
                "dy": p.dy,
                "dz": p.dz,
            }
            for p in r.placements
        ],
        "unpacked": [i.name for i in r.unpacked],
    }
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
