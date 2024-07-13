from __future__ import annotations

import dataclasses
from typing import Self


@dataclasses.dataclass(frozen=True)
class Colour:
    strokes: tuple[Stroke, ...]

    @classmethod
    def solid(cls, colour: str, thickness_multiplier: float = 1.0) -> Self:
        return cls(strokes=(Stroke(dashes=colour, thickness_multiplier=thickness_multiplier),))

    @classmethod
    def stroke(cls, stroke: Stroke) -> Self:
        return cls(strokes=(stroke,))


@dataclasses.dataclass(frozen=True)
class Stroke:
    dashes: str | tuple[str, ...]
    thickness_multiplier: float = 1.0
    dash_length: float = 1.0
