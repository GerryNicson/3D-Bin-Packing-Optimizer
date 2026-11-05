from __future__ import annotations

import argparse
import sys
from pathlib import Path

from binpacker.costs import naive_plan, savings
from binpacker.io import load_boxes, load_items
from binpacker.metrics import report
from binpacker.optimizer import select_box
from binpacker.visualize import plot_result


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser with the `pack` subcommand."""
    parser = argparse.ArgumentParser(prog="binpacker", description="3D bin packing optimizer (offline).")
    sub = parser.add_subparsers(dest="command", required=True)
    pack_parser = sub.add_parser("pack", help="pack items into boxes")
    pack_parser.add_argument("--items", required=True, help="path to the items file")
    pack_parser.add_argument("--boxes", required=True, help="path to the boxes file")
    pack_parser.add_argument("--plot", default=None, help="optional path for the plot image")
    pack_parser.add_argument("--seed", type=int, default=0, help="random seed (default 0)")
    pack_parser.add_argument("--shipments", type=int, default=1, help="shipments per month (default 1)")
    return parser


def _plot_paths(path: str, count: int) -> list[str]:
    """One PNG path per result; _1, _2... are added only when there are several."""
    if count == 1:
        return [path]
    p = Path(path)
    return [str(p.with_name(f"{p.stem}_{i}{p.suffix}")) for i in range(1, count + 1)]


def main(argv: list[str] | None = None) -> int:
    """Load, pack, print reports, cost and savings, optionally plot; 0 = ok, 1 = error."""
    args = build_parser().parse_args(argv)
    try:
        items = load_items(args.items)
        boxes = load_boxes(args.boxes)
        results = select_box(items, boxes, seed=args.seed)
        for result in results:
            print(report(result))
        out = savings(results, naive_plan(items, boxes), shipments_per_month=args.shipments)
        print(f"Total cost: {out['optimized_cost']:.2f}")
        print(
            f"Savings vs naive: {out['saving_per_shipment']:.2f} per shipment, "
            f"{out['saving_per_month']:.2f} per month ({out['saving_pct']:.1f}%)"
        )
        if args.plot:
            for result, path in zip(results, _plot_paths(args.plot, len(results))):
                plot_result(result, path=path)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
