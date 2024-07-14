from __future__ import annotations

import dataclasses
import itertools
import math
import uuid
from typing import TYPE_CHECKING

import vector
from rich.progress import track

if TYPE_CHECKING:
    from autocarter.colour import Colour


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
        for station in track(self.stations.values(), description="Finalising network"):
            station.calculate_tangent(self)
            station.calculate_adjacent_stations(self)
            station.calculate_line_coordinates(self)


@dataclasses.dataclass
class Station:
    name: str | set[str]
    coordinates: vector.Vector2D
    tangent: vector.Vector2D = dataclasses.field(default_factory=lambda: vector.obj(x=1, y=0))
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)
    line_coordinates: dict[uuid.UUID, float] = dataclasses.field(default_factory=dict)
    adjacent_stations: dict[uuid.UUID, list[list[uuid.UUID]]] = dataclasses.field(default_factory=dict)

    def merge_into(self, n: Network, s: Station):
        to_add = {}
        to_delete = []
        for (u, v), conn in n.connections.items():
            if u == self.id:
                nu, nv = sorted((s.id, v))
                to_add[nu, nv] = conn
                to_delete.append((u, v))
            if v == self.id:
                nu, nv = sorted((u, s.id))
                to_add[nu, nv] = conn
                to_delete.append((u, v))
        for k, v in to_add.items():
            n.connections.setdefault(k, set()).update(v)
        for k in to_delete:
            del n.connections[k]

        s.adjacent_stations.update(self.adjacent_stations)
        if isinstance(s.name, str):
            if isinstance(self.name, str):
                s.name = {s.name, self.name}
            else:
                s.name = {s.name, *self.name}
        elif isinstance(self.name, str):
            s.name.add(self.name)
        else:
            s.name.update(self.name)
        del n.stations[self.id]

    def connections(self, n: Network) -> list[tuple[Station, set[Connection | Line]]]:
        return [
            (
                n.stations[k[0] if self.id == k[1] else k[1]],
                {(vv if isinstance(vv, Connection) else n.lines[vv]) for vv in v},
            )
            for k, v in n.connections.items()
            if self.id in k
        ]

    def calculate_adjacent_stations(self, n: Network):
        for line in self.lines(n):
            if line.id in self.adjacent_stations:
                continue
            stations = [s for s, ls in self.connections(n) if line in ls]
            self.adjacent_stations[line.id] = [[a.id] for a in stations]

    def lines(self, n: Network) -> set[Line]:
        return {a for _, b in self.connections(n) for a in b if isinstance(a, Line)}

    def calculate_tangent(self, n: Network):
        conn = [ss for s, line in self.connections(n) for ss in (s,) * len([a for a in line if isinstance(a, Line)])]
        if len({(a.coordinates.x, a.coordinates.y) for a in conn}) == 1:
            self.tangent = (conn[0].coordinates - self.coordinates).unit().rotateZ(math.pi / 2)
        elif all(
            (a.coordinates - self.coordinates).dot(b.coordinates - self.coordinates) > 0
            for a, b in itertools.combinations(conn, 2)
        ):
            self.tangent = (
                sum(((a.coordinates - self.coordinates).unit() for a in conn), start=vector.obj(x=0, y=0))
                .unit()
                .rotateZ(math.pi / 2)
            )
        else:
            self.tangent = sum(
                ((a.coordinates - self.coordinates).unit() for a in conn), start=vector.obj(x=0, y=0)
            ).unit()
        if self.tangent == vector.obj(x=0, y=0) and len(conn) >= 1:
            self.tangent = (conn[0].coordinates - self.coordinates).unit().rotateZ(math.pi / 2)
        if self.tangent.x < 0 or (self.tangent.x == 0 and self.tangent.y < 0):
            self.tangent = -self.tangent

    def calculate_line_coordinates(self, n: Network):
        lines = self.lines(n)
        self.line_coordinates = {line.id: i - (len(lines) - 1) / 2 for i, line in enumerate(sorted(lines))}


@dataclasses.dataclass(frozen=True)
class Line:
    colour: Colour
    name: str
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)

    def __lt__(self, other):
        return self.name < other.name


@dataclasses.dataclass(frozen=True)
class Connection:
    pass
