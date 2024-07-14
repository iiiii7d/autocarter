from __future__ import annotations

import colorsys
import dataclasses
import functools
import re
from typing import Self

LIGHTNESS_THRESHOLD = 0.4


@dataclasses.dataclass(frozen=True)
class Colour:
    strokes: tuple[Stroke, ...]
    text_override: str | None = None

    @classmethod
    def solid(cls, colour: str, thickness_multiplier: float = 1.0) -> Self:
        return cls(strokes=(Stroke(dashes=colour, thickness_multiplier=thickness_multiplier),))

    @classmethod
    def stroke(cls, stroke: Stroke) -> Self:
        return cls(strokes=(stroke,))

    @functools.cached_property
    def text(self) -> str:
        if self.text_override is not None:
            return self.text_override
        colour = self.strokes[0].dashes[0] if isinstance(self.strokes[0].dashes, tuple) else self.strokes[0].dashes
        match = re.search(r"^#(.)(.)(.)$|^#(..)(..)(..)$", colour)
        if match is None:
            return "#000"
        r = int(2 * match.group(1) if match.group(1) is not None else match.group(4), 16)
        g = int(2 * match.group(2) if match.group(2) is not None else match.group(5), 16)
        b = int(2 * match.group(3) if match.group(3) is not None else match.group(6), 16)
        lightness = colorsys.rgb_to_hls(r / 256, g / 256, b / 256)[1]
        return "#000" if lightness > LIGHTNESS_THRESHOLD else "#fff"


@dataclasses.dataclass(frozen=True)
class Stroke:
    dashes: str | tuple[str, ...]
    thickness_multiplier: float = 1.0
    dash_length: float = 1.0
