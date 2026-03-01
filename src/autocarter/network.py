from __future__ import annotations

import dataclasses
import itertools
import math
import uuid
from abc import abstractmethod
from collections.abc import Hashable
from typing import TYPE_CHECKING, Protocol, Self

from rich.progress import track
from rustworkx.rustworkx import PyGraph

from autocarter.vector import Vector

if TYPE_CHECKING:
    from autocarter.colour import Colour


class ID(Protocol, Hashable):
    @abstractmethod
    def __lt__(self, other: Self):
        pass


@dataclasses.dataclass
class Network:
    g: PyGraph[Station, Line | Connection] = dataclasses.field(default_factory=lambda: PyGraph(multigraph=True))
    station_id2index: dict[ID, int] = dataclasses.field(default_factory=dict)
    lines: list[Line] = dataclasses.field(default_factory=list)

    def add_line(self, line: Line) -> Line:
        self.lines.append(line)
        return line

    def line(self, i: ID) -> Line:
        return next(a for a in self.lines if a.id == i)

    def add_station(self, station: Station) -> Station:
        idx = self.g.add_node(station)
        self.station_id2index[station.id] = idx
        return station

    def station(self, i: ID) -> Station:
        return self.g.get_node_data(self.station_id2index[i])

    def connect(self, u: Station, v: Station, line: Line | Connection):
        self.g.add_edge(self.station_id2index[u.id], self.station_id2index[v.id], line)

    def finalise(self):
        for station in track(self.g.nodes(), description="Finalising network"):
            station.calculate_tangent(self)
            station.calculate_adjacent_stations(self)
            station.calculate_line_coordinates(self)


@dataclasses.dataclass
class Station:
    name: str | set[str]
    coordinates: Vector
    tangent: Vector = Vector(1, 0)  # noqa: RUF009
    id: ID = dataclasses.field(default_factory=uuid.uuid4)
    line_coordinates: dict[ID, float] = dataclasses.field(default_factory=dict)
    adjacent_stations: dict[ID, list[list[ID]]] = dataclasses.field(default_factory=dict)

    def merge_into(self, n: Network, s: Station):
        for edge in n.g.edge_indices_from_endpoints(n.station_id2index[self.id], n.station_id2index[s.id]):
            n.g.remove_edge_from_index(edge)
        idx = n.g.contract_nodes((n.station_id2index[self.id], n.station_id2index[s.id]), s)
        n.station_id2index[self.id] = idx
        n.station_id2index[s.id] = idx

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

    def calculate_adjacent_stations(self, n: Network):
        pre_existing_lines = set(self.adjacent_stations.keys())
        for _, sidx, line in n.g.out_edges(n.station_id2index[self.id]):
            if isinstance(line, Connection) or line.id in pre_existing_lines:
                continue
            station = n.g.get_node_data(sidx)
            self.adjacent_stations.setdefault(line.id, []).append([station.id])

    def lines(self, n: Network) -> set[Line]:
        return {line for _, _, line in n.g.out_edges(n.station_id2index[self.id]) if isinstance(line, Line)}

    def calculate_tangent(self, n: Network):
        conn = [n.g.get_node_data(s) for _, s, _ in n.g.out_edges(n.station_id2index[self.id])]
        if len({(a.coordinates.x, a.coordinates.y) for a in conn}) == 1:
            self.tangent = (conn[0].coordinates - self.coordinates).unit.rotate(math.pi / 2)
        elif all(
            (a.coordinates - self.coordinates).dot(b.coordinates - self.coordinates) > 0
            for a, b in itertools.combinations(conn, 2)
        ):
            self.tangent = sum(((a.coordinates - self.coordinates).unit for a in conn), start=Vector(0)).unit.rotate(
                math.pi / 2
            )
        else:
            self.tangent = sum(((a.coordinates - self.coordinates).unit for a in conn), start=Vector(0)).unit
        if self.tangent == Vector(0) and len(conn) >= 1:
            self.tangent = (conn[0].coordinates - self.coordinates).unit.rotate(math.pi / 2)
        if self.tangent.x < 0 or (self.tangent.x == 0 and self.tangent.y < 0):
            self.tangent = -self.tangent

    def calculate_line_coordinates(self, n: Network):
        lines = self.lines(n)
        lc = [0.0]
        for prev_line, line in itertools.pairwise(lines):
            lc.append(
                lc[-1] + line.colour.max_thickness_multiplier() / 2 + prev_line.colour.max_thickness_multiplier() / 2
            )
        self.line_coordinates = {line.id: c - lc[-1] / 2 for line, c in zip(lines, lc)}


@dataclasses.dataclass(frozen=True)
class Line:
    colour: Colour
    name: str
    id: ID = dataclasses.field(default_factory=uuid.uuid4)

    def __lt__(self, other):
        return self.name < other.name


@dataclasses.dataclass(frozen=True)
class Connection:
    pass
