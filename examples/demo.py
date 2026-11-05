"""Demo: pack the sample items into the largest sample box and save a picture."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from binpacker.io import load_boxes, load_items  # noqa: E402
from binpacker.metrics import report  # noqa: E402
from binpacker.packer import pack  # noqa: E402
from binpacker.visualize import plot_result  # noqa: E402

items = load_items(ROOT / "data" / "sample_items.json")
box = max(load_boxes(ROOT / "data" / "sample_boxes.json"), key=lambda b: b.volume)
result = pack(items, box)
print(report(result))
plot_result(result, path=ROOT / "demo_output.png")
