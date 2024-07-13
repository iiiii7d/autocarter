from __future__ import annotations

import dataclasses

import vector


@dataclasses.dataclass
class Style:
    line_thickness: float = 2.0
    padding: float = 64.0
    scale: float = 1.0
    offset: vector.Vector2D = dataclasses.field(default_factory=lambda: vector.obj(x=0, y=0))
    stiffness: float = 3.0
    station_dots: bool = False
