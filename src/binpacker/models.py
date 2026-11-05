"""Data models: items, boxes, placements and packing results."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Item:
    """A cuboid item (cm, kg)."""

    name: str
    length: float
    width: float
    height: float
    weight: float = 0.0
    quantity: int = 1
    allow_rotation: bool = True

    def __post_init__(self) -> None:
        """Raise ValueError naming the first invalid field."""
        if not self.name.strip():
            raise ValueError("name must not be empty")
        for dim in ("length", "width", "height"):
            if getattr(self, dim) <= 0:
                raise ValueError(f"{dim} must be > 0")
        if self.weight < 0:
            raise ValueError("weight must be >= 0")
        if self.quantity < 1:
            raise ValueError("quantity must be >= 1")

    @property
    def volume(self) -> float:
        """Return length * width * height."""
        return self.length * self.width * self.height


@dataclass(frozen=True)
class Box:
    """A container box (cm, kg) with a weight limit and a cost."""

    name: str
    length: float
    width: float
    height: float
    max_weight: float = float("inf")
    cost: float = 0.0

    def __post_init__(self) -> None:
        """Raise ValueError naming the first invalid field."""
        if not self.name.strip():
            raise ValueError("name must not be empty")
        for dim in ("length", "width", "height"):
            if getattr(self, dim) <= 0:
                raise ValueError(f"{dim} must be > 0")
        if self.max_weight <= 0:
            raise ValueError("max_weight must be > 0")
        if self.cost < 0:
            raise ValueError("cost must be >= 0")

    @property
    def volume(self) -> float:
        """Return length * width * height."""
        return self.length * self.width * self.height


@dataclass
class Placement:
    """An item placed at (x, y, z) with oriented size (dx, dy, dz)."""

    item: Item
    x: float
    y: float
    z: float
    dx: float
    dy: float
    dz: float

    @property
    def x2(self) -> float:
        """Far corner along x."""
        return self.x + self.dx

    @property
    def y2(self) -> float:
        """Far corner along y."""
        return self.y + self.dy

    @property
    def z2(self) -> float:
        """Far corner along z."""
        return self.z + self.dz

    @property
    def volume(self) -> float:
        """Return dx * dy * dz."""
        return self.dx * self.dy * self.dz


@dataclass
class PackingResult:
    """The outcome of packing items into one box."""

    box: Box
    placements: list[Placement] = field(default_factory=list)
    unpacked: list[Item] = field(default_factory=list)
