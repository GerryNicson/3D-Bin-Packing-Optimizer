from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from binpacker.io import load_boxes, load_items  # noqa: E402
from binpacker.metrics import utilization  # noqa: E402
from binpacker.models import Item  # noqa: E402
from binpacker.optimizer import best_pack  # noqa: E402
from binpacker.packer import pack  # noqa: E402


def _random_sets(count: int = 5) -> list[list[Item]]:
    """Return `count` seeded random item sets (15-30 items, sides 3-15 cm)."""
    rng = random.Random(42)
    sets = []
    for _ in range(count):
        n = rng.randint(15, 30)
        sets.append([
            Item(f"r{k}", rng.randint(3, 15), rng.randint(3, 15), rng.randint(3, 15))
            for k in range(1, n + 1)
        ])
    return sets


def _score(r) -> tuple:
    """Same ranking as the optimizer: fewer unpacked first, then utilization."""
    return (-len(r.unpacked), utilization(r))


def main() -> None:
    """Compare pack vs best_pack on the sample data and 5 random sets."""
    items = load_items(ROOT / "data" / "sample_items.json")
    box = max(load_boxes(ROOT / "data" / "sample_boxes.json"), key=lambda b: b.volume)
    cases = [("sample", items)]
    cases += [(f"random {i}", s) for i, s in enumerate(_random_sets(), 1)]

    print(f"Box: {box.name} ({box.length} x {box.width} x {box.height} cm)")
    print(f"{'case':<10}| {'pack util %':>11} | {'best util %':>11} "
          f"| {'unpacked (pack)':>15} | {'unpacked (best)':>15}")
    better = worse = 0
    for name, case_items in cases:
        plain = pack(case_items, box)
        best = best_pack(case_items, box)
        if _score(best) > _score(plain):
            better += 1
        elif _score(best) < _score(plain):
            worse += 1
        print(f"{name:<10}| {utilization(plain) * 100:>11.1f} | {utilization(best) * 100:>11.1f} "
              f"| {len(plain.unpacked):>15} | {len(best.unpacked):>15}")

    total = len(cases)
    if worse:
        print(f"WARNING: best_pack was worse than pack in {worse} of {total} cases.")
    elif better:
        print(f"best_pack improved {better} of {total} cases and was never worse.")
    else:
        print(f"No improvement: best_pack matched pack in all {total} cases.")


if __name__ == "__main__":
    main()
