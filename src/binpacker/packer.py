"""Core packing algorithm that places items into a box."""
from __future__ import annotations

# Extreme Points: instead of testing every position, only try "corner" points.
# Start with one point, the origin (0, 0, 0). After an item is placed, its 3 far
# corners (x2, y, z), (x, y2, z) and (x, y, z2) become new candidate points.
# A point that now lies inside a placed item is blocked, so it is dropped.
# Points are tried in order of z, then y, then x, so the box fills from the bottom up.

from binpacker.geometry import inside, orientations, overlaps
from binpacker.models import Box, Item, PackingResult, Placement


def _sort_items(items: list[Item]) -> list[Item]:
    """Sort items by volume descending, ties broken by name."""
    return sorted(items, key=lambda item: (-item.volume, item.name))


def _fits(p: Placement, placed: list[Placement], box: Box) -> bool:
    """Return True if p is inside the box and overlaps none of the placed items."""
    return inside(p, box) and not any(overlaps(p, q) for q in placed)


def _find_position(
    item: Item,
    placed: list[Placement],
    points: list[tuple[float, float, float]],
    box: Box,
) -> Placement | None:
    """Return the first Placement of item that fits at a candidate point, else None."""
    for x, y, z in sorted(points, key=lambda pt: (pt[2], pt[1], pt[0])):
        for dx, dy, dz in orientations(item):
            p = Placement(item, x, y, z, dx, dy, dz)
            if _fits(p, placed, box):
                return p
    return None


def _update_points(
    points: list[tuple[float, float, float]],
    new: Placement,
    placed: list[Placement],
) -> list[tuple[float, float, float]]:
    """Add the 3 corner points of new, drop duplicates and blocked points, return sorted."""
    candidates = set(points)
    candidates.update([(new.x2, new.y, new.z), (new.x, new.y2, new.z), (new.x, new.y, new.z2)])
    free = [
        (px, py, pz)
        for px, py, pz in candidates
        if not any(q.x <= px < q.x2 and q.y <= py < q.y2 and q.z <= pz < q.z2 for q in placed)
    ]
    return sorted(free)


def pack(items: list[Item], box: Box, presorted: bool = False) -> PackingResult:
    """Place items into the box one by one; items that do not fit go to unpacked."""
    ordered = list(items) if presorted else _sort_items(items)
    points = [(0, 0, 0)]
    placed: list[Placement] = []
    unpacked: list[Item] = []
    packed_weight = 0.0
    for item in ordered:
        if packed_weight + item.weight > box.max_weight:
            unpacked.append(item)
            continue
        p = _find_position(item, placed, points, box)
        if p is None:
            unpacked.append(item)
        else:
            placed.append(p)
            packed_weight += item.weight
            points = _update_points(points, p, placed)
    return PackingResult(box, placed, unpacked)
