from __future__ import annotations

import random
from typing import TYPE_CHECKING, Callable

from binpacker.metrics import utilization
from binpacker.models import Item
from binpacker.packer import pack

if TYPE_CHECKING:
    from binpacker.models import Box, PackingResult

STRATEGIES: dict[str, Callable[[Item], float]] = {
    "volume": lambda item: item.volume,
    "longest_side": lambda item: max(item.length, item.width, item.height),
    "height": lambda item: item.height,
    "weight": lambda item: item.weight,
}


def _strategy_orders(items: list[Item]) -> list[list[Item]]:
    """Return one list per strategy, sorted descending by its key (tie: name)."""
    return [sorted(items, key=lambda i: (-key(i), i.name)) for key in STRATEGIES.values()]


def _score(r: PackingResult) -> tuple:
    """Larger is better: (-number unpacked, utilization)."""
    return (-len(r.unpacked), utilization(r))


def best_pack(items: list[Item], box: Box, seed: int = 0, restarts: int = 20) -> PackingResult:
    """Best result of every strategy order plus `restarts` seeded random shuffles."""
    rng = random.Random(seed)
    results = [pack(order, box, presorted=True) for order in _strategy_orders(items)]
    best = max(results, key=_score)
    for _ in range(restarts):
        order = list(items)
        rng.shuffle(order)
        result = pack(order, box, presorted=True)
        if _score(result) > _score(best):
            best = result
    return best


def select_box(items: list[Item], boxes: list[Box], seed: int = 0) -> list[PackingResult]:
    """Cheapest single box that fits all, else rounds of the largest box on the leftovers."""
    tried = []
    for box in sorted(boxes, key=lambda b: (b.cost, b.volume)):
        result = best_pack(items, box, seed=seed)
        if not result.unpacked:
            return [result]
        tried.append((box, result))
    largest, result = max(tried, key=lambda pair: pair[0].volume)
    results = [result]
    while result.unpacked:
        result = best_pack(result.unpacked, largest, seed=seed)
        if not result.placements:
            break
        results.append(result)
    return results
