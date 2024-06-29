from __future__ import annotations

import dataclasses
import math
import uuid

import vector


@dataclasses.dataclass
class Graph:
    lines: dict[uuid.UUID, Line]
    stations: dict[uuid.UUID, Station]
    connections: dict[tuple[uuid.UUID, uuid.UUID], set[uuid.UUID | Connection]]


@dataclasses.dataclass
class Station:
    name: str
    coordinates: vector.Vector2D
    tangent: vector.Vector2D = dataclasses.field(default_factory=lambda: vector.obj(x=1, y=0))
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)


    def connections(self, g: Graph) -> list[tuple[Station, set[Connection | Line]]]:
        return [(g.stations[k[0] if self.id == k[1] else k[1]],
                 {vv if isinstance(vv, Connection) else g.lines[vv] for vv in v}) for k, v in g.connections.items() if
                self.id in k]

    def lines(self, g: Graph) -> set[Line]:
        return {a for _, b in self.connections(g) for a in b if isinstance(a, Line)}

    def calculate_tangent(self, g: Graph):
        conn = self.connections(g)
        if len(conn) == 1:
            self.tangent = (conn[0][0].coordinates - self.coordinates).unit().rotateZ(math.pi / 2)
        else:
            self.tangent = sum(((a.coordinates - self.coordinates).unit() for a, _ in conn),
                               start=vector.obj(x=0, y=0)).unit()

    def lines(self, g: Graph):


@dataclasses.dataclass
class Line:
    colour: str
    name: str
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)


@dataclasses.dataclass
class Connection:
    pass
