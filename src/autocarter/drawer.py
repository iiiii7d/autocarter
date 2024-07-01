from __future__ import annotations

import dataclasses
import math

import svg
import vector

from autocarter.network import Connection, Line, Network, Station


@dataclasses.dataclass
class Style:
    line_thickness: float = 2.0
    padding: float = 10.0
    scale: float = 1.0
    offset: vector.Vector2D = dataclasses.field(default_factory=lambda: vector.obj(x=0, y=0))
    stiffness: float = 8.0


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
                    for (u, v), lines in self.n.connections.items()
                ),
                *(self.draw_station(s) for s in self.n.stations.values()),
            ],
        )

    def draw_connection(self, u: Station, v: Station, lines: set[Line | Connection]) -> svg.Element:
        elements = []
        for line in lines:
            nu = self.move_vec(u.coordinates) + u.line_coordinates[line.id] * self.s.line_thickness * u.tangent
            nv = self.move_vec(v.coordinates) + v.line_coordinates[line.id] * self.s.line_thickness * v.tangent

            uc = u.connections2(self.n)[line]
            uo = None if len(uc) <= 1 else uc[0] if uc[1].coordinates == v.coordinates else uc[1]
            vc = v.connections2(self.n)[line]
            vo = None if len(vc) <= 1 else vc[0] if vc[1].coordinates == u.coordinates else vc[1]

            if len(uc) > 1:
                n1 = (v.coordinates - uo.coordinates) / self.s.stiffness * self.s.scale
            else:
                n1 = (v.coordinates - u.coordinates) / self.s.stiffness * self.s.scale

            if len(vc) > 1:
                n2 = (u.coordinates - vo.coordinates) / self.s.stiffness * self.s.scale
            else:
                n2 = (u.coordinates - v.coordinates) / self.s.stiffness * self.s.scale

            elements.append(
                svg.Path(
                    stroke=line.colour,
                    stroke_width=self.s.line_thickness,
                    fill_opacity=0,
                    d=[
                        svg.M(nu.x, nu.y),
                        svg.C(nu.x + n1.x, nu.y + n1.y, nv.x + n2.x, nv.y + n2.y, nv.x, nv.y),
                    ],
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
        return svg.G(
            elements=[
                svg.Path(
                    stroke="#000",
                    stroke_width=5.0,
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
                # svg.Circle(
                #     fill="#ffffff",
                #     stroke="#000000",
                #     stroke_width=1.5,
                #     cx=c.x,
                #     cy=c.y,
                #     r=2.5
                # ),
                svg.Text(
                    text=station.name,
                    x=t.x,
                    y=t.y,
                    font_size=3,
                    text_anchor="start",
                    transform=[
                        svg.Rotate(
                            station.tangent.phi / math.pi * 180,
                            (c1 if c1.x > c2.x else c2).x,
                            (c1 if c1.x > c2.x else c2).y,
                        )
                    ],
                ),
            ]
        )
