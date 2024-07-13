from __future__ import annotations

import dataclasses
from typing import Self

import svg

from autocarter.style import Style


@dataclasses.dataclass(frozen=True)
class Colour:
    strokes: tuple[Stroke, ...]

    @classmethod
    def solid(cls, colour: str, thickness_multiplier: float = 1.0) -> Self:
        return cls(strokes=(Stroke(dashes=colour, thickness_multiplier=thickness_multiplier),))

    @classmethod
    def stroke(cls, stroke: Stroke) -> Self:
        return cls(strokes=(stroke,))

    def svg(self, s: Style, i: str | None = None, d: list[svg.PathData] | None = None):
        elements = []
        for stroke in self.strokes:
            if isinstance(stroke.dashes, str):
                elements.append(
                    svg.Path(
                        stroke=stroke.dashes,
                        stroke_width=stroke.thickness_multiplier * s.line_thickness,
                        fill_opacity=0,
                        id=i,
                        d=d,
                    )
                )
            else:
                for offset, colours in enumerate(stroke.dashes):
                    elements.append(
                        svg.Path(
                            stroke=colours,
                            stroke_dasharray=[
                                stroke.dash_length * s.line_thickness,
                                stroke.dash_length * s.line_thickness * (len(stroke.dashes) - 1),
                            ],
                            stroke_dashoffset=stroke.dash_length * offset * s.line_thickness,
                            stroke_width=stroke.thickness_multiplier * s.line_thickness,
                            fill_opacity=0,
                            id=i,
                            d=d,
                        )
                    )
        return svg.G(elements=elements)


@dataclasses.dataclass(frozen=True)
class Stroke:
    dashes: str | tuple[str, ...]
    thickness_multiplier: float = 1.0
    dash_length: float = 1.0
