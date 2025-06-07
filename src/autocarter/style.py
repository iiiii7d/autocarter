from __future__ import annotations

import dataclasses

from autocarter.vector import Vector


@dataclasses.dataclass
class Style:
    line_thickness: float = 2.0
    padding: float = 64.0
    scale: float = 1.0
    offset: Vector = Vector(0)  # noqa: RUF009
    stiffness: float = 3.0
    station_dots: bool = False
