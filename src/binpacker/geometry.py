"""Geometry helpers: orientations, overlap, containment and validation."""
from __future__ import annotations

from itertools import combinations, permutations

from binpacker.models import Box, Item, PackingResult, Placement

EPS = 1e-9


def orientations(item: Item) -> list[tuple[float, float, float]]:
    """Return the unique (dx, dy, dz) orientations of an item, at most 6."""
    dims = (item.length, item.width, item.height)
    if not item.allow_rotation:
        return [dims]
    return list(dict.fromkeys(permutations(dims)))


def overlaps(a: Placement, b: Placement) -> bool:
    """Return True if the interiors of a and b intersect; touching faces do not."""
    return (
        a.x < b.x2 - EPS and b.x < a.x2 - EPS
        and a.y < b.y2 - EPS and b.y < a.y2 - EPS
        and a.z < b.z2 - EPS and b.z < a.z2 - EPS
    )


def inside(p: Placement, box: Box) -> bool:
    """Return True if the placement lies completely within the box."""
    return (
        p.x >= -EPS and p.y >= -EPS and p.z >= -EPS
        and p.x2 <= box.length + EPS
        and p.y2 <= box.width + EPS
        and p.z2 <= box.height + EPS
    )


def validate_result(r: PackingResult) -> list[str]:
    """Return messages for placements outside the box, overlapping pairs and overweight."""
    errors = []
    for p in r.placements:
        if not inside(p, r.box):
            errors.append(f"{p.item.name} is outside the box")
    for a, b in combinations(r.placements, 2):
        if overlaps(a, b):
            errors.append(f"{a.item.name} overlaps {b.item.name}")
    total = sum(p.item.weight for p in r.placements)
    if total > r.box.max_weight + EPS:
        errors.append(f"total weight {total:g} kg exceeds the limit of {r.box.max_weight:g} kg")
    return errors
