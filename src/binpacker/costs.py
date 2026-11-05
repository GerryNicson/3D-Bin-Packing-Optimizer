from __future__ import annotations

from typing import TYPE_CHECKING

from binpacker.metrics import total_weight
from binpacker.packer import pack

if TYPE_CHECKING:
    from binpacker.models import Box, Item, PackingResult


def dimensional_weight(box: Box, divisor: float = 5000) -> float:
    """Volumetric weight in kg: length * width * height / divisor."""
    return box.volume / divisor


def shipping_cost(r: PackingResult, rate_per_kg: float = 1.0, divisor: float = 5000) -> float:
    """Billable weight (larger of packed and dimensional weight) times the rate per kg."""
    return max(total_weight(r), dimensional_weight(r.box, divisor)) * rate_per_kg


def total_cost(r: PackingResult, rate_per_kg: float = 1.0, divisor: float = 5000) -> float:
    """Box cost plus shipping cost."""
    return r.box.cost + shipping_cost(r, rate_per_kg, divisor)


def naive_plan(items: list[Item], boxes: list[Box]) -> list[PackingResult]:
    """Baseline: always the largest box with plain pack(); leftovers go into new boxes."""
    largest = max(boxes, key=lambda b: b.volume)
    result = pack(items, largest)
    results = [result]
    while result.unpacked:
        result = pack(result.unpacked, largest)
        if not result.placements:
            break
        results.append(result)
    return results


def savings(
    optimized: list[PackingResult],
    naive: list[PackingResult],
    shipments_per_month: float = 1,
    rate_per_kg: float = 1.0,
    divisor: float = 5000,
) -> dict:
    """Compare two plans (lists of results); saving_pct is a percentage of the naive cost."""
    optimized_cost = sum(total_cost(r, rate_per_kg, divisor) for r in optimized)
    naive_cost = sum(total_cost(r, rate_per_kg, divisor) for r in naive)
    saving = naive_cost - optimized_cost
    return {
        "optimized_cost": optimized_cost,
        "naive_cost": naive_cost,
        "saving_per_shipment": saving,
        "saving_per_month": saving * shipments_per_month,
        "saving_pct": saving / naive_cost * 100 if naive_cost else 0.0,
    }
