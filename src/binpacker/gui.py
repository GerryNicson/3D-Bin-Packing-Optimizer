from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable

from binpacker.costs import naive_plan, savings
from binpacker.io import expand_quantity, load_boxes, load_items
from binpacker.metrics import report
from binpacker.models import Box, Item
from binpacker.optimizer import select_box

if TYPE_CHECKING:
    from tkinter import ttk


def _name(text: str, label: str) -> str:
    """A name cell must not be empty."""
    name = text.strip()
    if not name:
        raise ValueError(f"{label}: name is required")
    return name


def _num(text: str, label: str, field: str, default: float | None = None) -> float:
    """Parse a number cell; an empty cell gives `default` (an error when there is none)."""
    text = text.strip()
    if not text:
        if default is None:
            raise ValueError(f"{label}: {field} is required")
        return default
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"{label}: {field} must be a number, got {text!r}") from None


def _whole(text: str, label: str, field: str, default: int) -> int:
    """Parse a whole-number cell; an empty cell gives `default`."""
    text = text.strip()
    try:
        return int(text) if text else default
    except ValueError:
        raise ValueError(f"{label}: {field} must be a whole number, got {text!r}") from None


def build_inputs(item_rows: list[list[str]], box_rows: list[list[str]]) -> tuple[list[Item], list[Box]]:
    """Turn the string rows of the form into expanded Items and Boxes; ValueError names the row and field."""
    items: list[Item] = []
    for i, (name, length, width, height, weight, qty) in enumerate(item_rows, 1):
        label = f"item row {i}"
        n = _name(name, label)
        dims = [_num(length, label, "length"), _num(width, label, "width"), _num(height, label, "height")]
        kg = _num(weight, label, "weight", 0.0)
        count = _whole(qty, label, "quantity", 1)
        try:
            item = Item(n, *dims, weight=kg, quantity=count)
        except ValueError as exc:
            raise ValueError(f"{label}: {exc}") from exc
        items.extend(expand_quantity(item))
    boxes: list[Box] = []
    for i, (name, length, width, height, max_weight, cost) in enumerate(box_rows, 1):
        label = f"box row {i}"
        n = _name(name, label)
        dims = [_num(length, label, "length"), _num(width, label, "width"), _num(height, label, "height")]
        limit = _num(max_weight, label, "max_weight", math.inf)
        price = _num(cost, label, "cost", 0.0)
        try:
            boxes.append(Box(n, *dims, max_weight=limit, cost=price))
        except ValueError as exc:
            raise ValueError(f"{label}: {exc}") from exc
    return items, boxes


def _fmt(value: float) -> str:
    """Show whole numbers without the trailing '.0'."""
    return str(int(value)) if value == int(value) else str(value)


def _item_cells(items: list[Item]) -> list[list[str]]:
    """Table rows for loaded items; the 'name#n' copies made by expand_quantity merge back into one row."""
    rows: list[list[str]] = []
    for item in items:
        base, sep, tail = item.name.rpartition("#")
        name = base if sep and tail.isdigit() else item.name
        cells = [name, _fmt(item.length), _fmt(item.width), _fmt(item.height), _fmt(item.weight)]
        if rows and rows[-1][:5] == cells:
            rows[-1][5] = str(int(rows[-1][5]) + 1)
        else:
            rows.append(cells + ["1"])
    return rows


def _box_cells(boxes: list[Box]) -> list[list[str]]:
    """Table rows for loaded boxes; an unlimited max weight is shown as an empty cell."""
    return [
        [
            b.name,
            _fmt(b.length),
            _fmt(b.width),
            _fmt(b.height),
            "" if math.isinf(b.max_weight) else _fmt(b.max_weight),
            _fmt(b.cost),
        ]
        for b in boxes
    ]


def _cost_text(plan: dict) -> str:
    """One line with the total cost and the saving against the naive plan."""
    return (
        f"Total cost: {plan['optimized_cost']:.2f} (naive: {plan['naive_cost']:.2f}) | "
        f"Saving: {plan['saving_per_shipment']:.2f} per shipment ({plan['saving_pct']:.1f}%)"
    )


def _make_table(
    parent: ttk.Frame,
    title: str,
    headers: list[str],
    load_text: str,
    loader: Callable[[str], list[list[str]]],
) -> tuple[ttk.LabelFrame, list[list[ttk.Entry]]]:
    """A titled table of Entry rows with Add, Remove and Load buttons; returns (frame, rows)."""
    from tkinter import filedialog, messagebox, ttk

    frame = ttk.LabelFrame(parent, text=title)
    grid = ttk.Frame(frame)
    grid.pack(fill="x", padx=5, pady=5)
    for col, head in enumerate(headers):
        ttk.Label(grid, text=head).grid(row=0, column=col)
    rows: list[list[ttk.Entry]] = []

    def add_row(values: list[str] | None = None) -> None:
        entries = [ttk.Entry(grid, width=11) for _ in headers]
        for col, entry in enumerate(entries):
            entry.grid(row=len(rows) + 1, column=col, padx=1, pady=1)
            if values:
                entry.insert(0, values[col])
        rows.append(entries)

    def remove_row() -> None:
        if rows:
            for entry in rows.pop():
                entry.destroy()

    def load() -> None:
        path = filedialog.askopenfilename(title=load_text, filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            data = loader(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Cannot load file", str(exc))
            return
        while rows:
            remove_row()
        for values in data:
            add_row(values)

    buttons = ttk.Frame(frame)
    buttons.pack(fill="x", padx=5, pady=(0, 5))
    ttk.Button(buttons, text="Add row", command=add_row).pack(side="left")
    ttk.Button(buttons, text="Remove last row", command=remove_row).pack(side="left", padx=5)
    ttk.Button(buttons, text=load_text, command=load).pack(side="left")
    add_row()
    return frame, rows


def main() -> None:
    """Open the window: load JSON into the tables, press Pack to see a report, a plot and the cost per box."""
    import tkinter as tk
    from tkinter import messagebox, ttk

    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    from binpacker.visualize import make_figure

    root = tk.Tk()
    root.title("3D Bin Packing Optimizer")
    left = ttk.Frame(root)
    left.pack(side="left", fill="y", padx=8, pady=8)
    right = ttk.Frame(root)
    right.pack(side="left", fill="both", expand=True, padx=8, pady=8)

    items_frame, item_rows = _make_table(
        left, "Items", ["Name", "Length", "Width", "Height", "Weight", "Qty"],
        "Load items", lambda path: _item_cells(load_items(path)),
    )
    items_frame.pack(fill="x", pady=(0, 8))
    boxes_frame, box_rows = _make_table(
        left, "Boxes", ["Name", "Length", "Width", "Height", "Max weight", "Cost"],
        "Load boxes", lambda path: _box_cells(load_boxes(path)),
    )
    boxes_frame.pack(fill="x", pady=(0, 8))

    text_frame = ttk.Frame(right)
    text_frame.pack(fill="x")
    output = tk.Text(text_frame, height=16, width=60)
    scroll = ttk.Scrollbar(text_frame, command=output.yview)
    output.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    output.pack(side="left", fill="both", expand=True)

    cost_var = tk.StringVar()
    ttk.Label(right, textvariable=cost_var).pack(anchor="w", pady=(8, 0))

    plot_frame = ttk.Frame(right, relief="sunken", borderwidth=1)
    plot_frame.pack(fill="both", expand=True, pady=(8, 0))
    fig = Figure(figsize=(5, 3.5))
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    widget = canvas.get_tk_widget()
    widget.pack(fill="both", expand=True)

    shown: list = []
    position = [0]
    page = tk.StringVar()
    nav = ttk.Frame(plot_frame)
    prev_btn = ttk.Button(nav, text="Prev", command=lambda: show(position[0] - 1))
    prev_btn.pack(side="left")
    ttk.Label(nav, textvariable=page).pack(side="left", padx=8)
    next_btn = ttk.Button(nav, text="Next", command=lambda: show(position[0] + 1))
    next_btn.pack(side="left")

    def show(index: int) -> None:
        """Draw result `index` on the canvas and update the page label and the Prev/Next buttons."""
        position[0] = index
        fig.clear()
        make_figure(shown[index], fig)
        canvas.draw()
        page.set(f"Box {index + 1} of {len(shown)}")
        prev_btn.state(["!disabled" if index > 0 else "disabled"])
        next_btn.state(["!disabled" if index < len(shown) - 1 else "disabled"])

    def run_pack() -> None:
        """Read both tables, pack, and show the reports, the cost and the plot; errors open a dialog."""
        try:
            items, boxes = build_inputs(
                [[entry.get() for entry in row] for row in item_rows],
                [[entry.get() for entry in row] for row in box_rows],
            )
            results = select_box(items, boxes)
            plan = savings(results, naive_plan(items, boxes))
        except ValueError as exc:
            messagebox.showerror("Cannot pack", str(exc))
            return
        output.delete("1.0", "end")
        output.insert("end", "\n\n".join(report(r) for r in results))
        shown[:] = results
        cost_var.set(_cost_text(plan) if shown else "")
        if len(shown) > 1:
            nav.pack(fill="x", before=widget)
        else:
            nav.pack_forget()
        if shown:
            show(0)

    ttk.Button(left, text="Pack", command=run_pack).pack(anchor="w")
    root.mainloop()


if __name__ == "__main__":
    main()
