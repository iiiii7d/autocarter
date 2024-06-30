from __future__ import annotations

import dataclasses
import math
import uuid

import vector


@dataclasses.dataclass
class Network:
    lines: dict[uuid.UUID, Line] = dataclasses.field(default_factory=dict)
    stations: dict[uuid.UUID, Station] = dataclasses.field(default_factory=dict)
    connections: dict[tuple[uuid.UUID, uuid.UUID], set[uuid.UUID | Connection]] = dataclasses.field(
        default_factory=dict
    )

    def add_line(self, line: Line) -> Line:
        self.lines[line.id] = line
        return line

    def add_station(self, station: Station) -> Station:
        self.stations[station.id] = station
        return station

    def connect(self, u: Station, v: Station, line: Line | Connection):
        nu, nv = sorted((u.id, v.id))
        self.connections.setdefault((nu, nv), set()).add(line.id if isinstance(line, Line) else line)

    def finalise(self):
        for station in self.stations.values():
            station.calculate_tangent(self)


@dataclasses.dataclass
class Station:
    name: str
    coordinates: vector.Vector2D
    tangent: vector.Vector2D = dataclasses.field(default_factory=lambda: vector.obj(x=1, y=0))
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)
    line_coordinates: dict[uuid.UUID, float] = dataclasses.field(default_factory=dict)

    def connections(self, n: Network) -> list[tuple[Station, set[Connection | Line]]]:
        return [
            (
                n.stations[k[0] if self.id == k[1] else k[1]],
                {(vv if isinstance(vv, Connection) else n.lines[vv]) for vv in v},
            )
            for k, v in n.connections.items()
            if self.id in k
        ]

    def connections2(self, n: Network) -> dict[Line, list[Station]]:
        return {line: [s for s, ls in self.connections(n) if line in ls] for line in self.lines(n)}

    def lines(self, n: Network) -> set[Line]:
        return {a for _, b in self.connections(n) for a in b if isinstance(a, Line)}

    def calculate_tangent(self, n: Network):
        conn = self.connections(n)
        if len(conn) == 1:
            self.tangent = (conn[0][0].coordinates - self.coordinates).unit().rotateZ(math.pi / 2)
        else:
            self.tangent = sum(
                ((a.coordinates - self.coordinates).unit() for a, _ in conn), start=vector.obj(x=0, y=0)
            ).unit()

    def calculate_line_coordinates(self, n: Network):
        lines = self.lines(n)
        self.line_coordinates = {line.id: i - (len(lines) - 1) / 2 for i, line in enumerate(lines)}


@dataclasses.dataclass(frozen=True)
class Line:
    colour: str
    name: str
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)


@dataclasses.dataclass(frozen=True)
class Connection:
    pass
