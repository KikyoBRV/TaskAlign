# models.py
from dataclasses import dataclass, field
from typing import List


@dataclass
class Machine:
    id: str
    name: str

    # Injection molding planning attributes
    group: str                 # "small" | "medium" | "large"
    tonnage: int               # machine tonnage capacity
    hours_per_day: float = 21.0
    efficiency: float = 0.85   # 0..1


@dataclass
class Mold:
    id: str
    name: str
    group: str       # must match machine.group
    tonnage: int     # must be <= machine.tonnage


@dataclass
class ProductComponent:
    id: str
    name: str

    quantity: int                 # pieces
    cycle_time_sec: float         # seconds per piece
    mold_id: str                  # which mold is required
    color: str                    # color/material
    due_day: int                  # day index in the month, 1..N
    lead_time_days: int = 2       # default 2 days

    prerequisites: List[str] = field(default_factory=list)
    status: str = "pending"