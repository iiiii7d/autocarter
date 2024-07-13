from __future__ import annotations

import dataclasses
import math
import uuid

import svg
import vector
from rich.progress import track

from autocarter.colour import Colour
from autocarter.network import Connection, Line, Network, Station
from autocarter.style import Style


@dataclasses.dataclass
class Drawer:
    n: Network
    s: Style

    def __init__(self, n: Network, s: Style | None = None):
        s = s or Style()
        for station in n.stations.values():
            station.calculate_line_coordinates(n)
        s.offset = vector.obj(
            x=min(s.coordinates.x for s in n.stations.values()), y=min(s.coordinates.y for s in n.stations.values())
        )
        self.n = n
        self.s = s

    def width_height(self) -> vector.Vector2D:
        xs = [s.coordinates.x for s in self.n.stations.values()]
        ys = [s.coordinates.y for s in self.n.stations.values()]
        return vector.obj(
            x=(max(xs) - min(xs)) * self.s.scale + 2 * self.s.padding,
            y=(max(ys) - min(ys)) * self.s.scale + 2 * self.s.padding,
        )

    def move_vec(self, c: vector.Vector2D) -> vector.Vector2D:
        return (c - self.s.offset) * self.s.scale + vector.obj(x=self.s.padding, y=self.s.padding)

    def draw(self) -> svg.SVG:
        wh = self.width_height()
        return svg.SVG(
            height=wh.y,
            width=wh.x,
            elements=[
                *(
                    self.draw_connection(
                        self.n.stations[u],
                        self.n.stations[v],
                        {line if isinstance(line, Connection) else self.n.lines[line] for line in lines},
                    )
                    for (u, v), lines in track(self.n.connections.items(), description="Drawing connections")
                ),
                *(self.draw_station(s) for s in track(self.n.stations.values(), description="Drawing stations")),
            ],
        )

    def _draw_strokes(self, colour: Colour, i: str | None = None, d: list[svg.PathData] | None = None):
        elements = []
        for stroke in colour.strokes:
            if isinstance(stroke.dashes, str):
                elements.append(
                    svg.Path(
                        stroke=stroke.dashes,
                        stroke_width=stroke.thickness_multiplier * self.s.line_thickness,
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
                                stroke.dash_length * self.s.line_thickness,
                                stroke.dash_length * self.s.line_thickness * (len(stroke.dashes) - 1),
                            ],
                            stroke_dashoffset=stroke.dash_length * offset * self.s.line_thickness,
                            stroke_width=stroke.thickness_multiplier * self.s.line_thickness,
                            fill_opacity=0,
                            id=i,
                            d=d,
                        )
                    )
        return svg.G(elements=elements)

    def draw_connection(self, u: Station, v: Station, lines: set[Line | Connection]) -> svg.Element:
        elements = []
        for line in lines:
            if isinstance(line, Connection):
                cu = self.move_vec(u.coordinates)
                cv = self.move_vec(v.coordinates)

                cu1 = cu + min(u.line_coordinates.values() or (0,)) * self.s.line_thickness * u.tangent
                cu2 = cu + max(u.line_coordinates.values() or (0,)) * self.s.line_thickness * u.tangent
                lu = cu1 if ((cu1 - cv).rho < (cu2 - cv).rho) else cu2

                cv1 = cv + min(v.line_coordinates.values() or (0,)) * self.s.line_thickness * v.tangent
                cv2 = cv + max(v.line_coordinates.values() or (0,)) * self.s.line_thickness * v.tangent
                lv = cv1 if ((cv1 - cu).rho < (cv2 - cu).rho) else cv2

                elements.append(
                    svg.Path(
                        stroke_width=self.s.line_thickness,
                        stroke="#888",
                        fill_opacity=0,
                        stroke_dasharray=[1, 1],
                        d=[
                            svg.M(lu.x, lu.y),
                            svg.L(lv.x, lv.y),
                        ],
                    ),
                )
                continue

            nu = self.move_vec(u.coordinates) + u.line_coordinates[line.id] * self.s.line_thickness * u.tangent
            nv = self.move_vec(v.coordinates) + v.line_coordinates[line.id] * self.s.line_thickness * v.tangent

            uc = u.connections2(self.n)[line]
            uo = (
                None
                if len(uc) <= 1 or line.id in u.terminus
                else uc[0]
                if uc[1].coordinates == v.coordinates
                else uc[1]
            )
            vc = v.connections2(self.n)[line]
            vo = (
                None
                if len(vc) <= 1 or line.id in v.terminus
                else vc[0]
                if vc[1].coordinates == u.coordinates
                else vc[1]
            )

            if uo is not None:
                n1 = (
                    (v.coordinates - uo.coordinates).unit()
                    * (v.coordinates - u.coordinates).rho
                    / self.s.stiffness
                    * self.s.scale
                )
            else:
                n1 = (v.coordinates - u.coordinates) / self.s.stiffness * self.s.scale

            if vo is not None:
                n2 = (
                    (u.coordinates - vo.coordinates).unit()
                    * (u.coordinates - v.coordinates).rho
                    / self.s.stiffness
                    * self.s.scale
                )
            else:
                n2 = (u.coordinates - v.coordinates) / self.s.stiffness * self.s.scale

            i = str(uuid.uuid4())
            elements.append(
                svg.G(
                    elements=[
                        self._draw_strokes(
                            line.colour,
                            i=i,
                            d=[
                                svg.M(nu.x, nu.y),
                                svg.C(nu.x + n1.x, nu.y + n1.y, nv.x + n2.x, nv.y + n2.y, nv.x, nv.y),
                            ],
                        ),
                        svg.Text(
                            font_size=3,
                            text_anchor="middle",
                            dy=1,
                            font_weight="bold",
                            font_family="sans-serif",
                            elements=[svg.TextPath(href="#" + i, text=line.name, startOffset="50%")],
                        ),
                    ]
                )
            )
        return svg.G(elements=elements)

    def draw_station(self, station: Station) -> svg.Element:
        c = self.move_vec(station.coordinates)
        c1 = c + min(station.line_coordinates.values() or (0,)) * self.s.line_thickness * station.tangent
        c2 = c + max(station.line_coordinates.values() or (0,)) * self.s.line_thickness * station.tangent
        t = (c1 if c1.x > c2.x else c2) + vector.obj(x=4, y=1)
        if t.x < c.x:
            t += 2 * (c - t)
        line_dots = []
        if self.s.station_dots:
            for line_uuid, n in station.line_coordinates.items():
                line = self.n.lines[line_uuid]
                cl = c + n * self.s.line_thickness * station.tangent
                for stroke in line.colour.strokes:
                    if isinstance(stroke.dashes, str):
                        line_dots.append(
                            svg.Circle(
                                cx=cl.x,
                                cy=cl.y,
                                r=stroke.thickness_multiplier,
                                fill=stroke.dashes,
                            )
                        )
                    else:
                        for offset, dash in enumerate(stroke.dashes):
                            line_dots.append(
                                svg.Circle(
                                    cx=cl.x,
                                    cy=cl.y,
                                    r=stroke.thickness_multiplier / 2,
                                    fill=None,
                                    stroke=dash,
                                    stroke_width=stroke.thickness_multiplier,
                                    stroke_dasharray=[
                                        math.tau * stroke.thickness_multiplier / len(stroke.dashes),
                                        math.tau * stroke.thickness_multiplier,
                                    ],
                                    stroke_dashoffset=math.tau * stroke.thickness_multiplier / offset,
                                )
                            )
        return svg.G(
            elements=[
                svg.Path(
                    stroke="#000",
                    stroke_width=3.5 if self.s.station_dots else 5.0,
                    stroke_linecap="round",
                    d=[
                        svg.M(c1.x, c1.y),
                        svg.L(c2.x, c2.y),
                    ],
                ),
                svg.Path(
                    stroke="#fff",
                    stroke_width=2.5,
                    stroke_linecap="round",
                    d=[
                        svg.M(c1.x, c1.y),
                        svg.L(c2.x, c2.y),
                    ],
                ),
                svg.Text(
                    text=station.name if isinstance(station.name, str) else " / ".join(sorted(list(station.name))),
                    x=t.x,
                    y=t.y,
                    font_size=3,
                    font_family="sans-serif",
                    text_anchor="start",
                    transform=[
                        svg.Rotate(
                            station.tangent.phi / math.pi * 180,
                            (c1 if c1.x > c2.x else c2).x,
                            (c1 if c1.x > c2.x else c2).y,
                        )
                    ],
                ),
                *line_dots,
            ]
        )
