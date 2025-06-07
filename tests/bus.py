import itertools
import json
import random

from autocarter.colour import Colour
from autocarter.drawer import Drawer
from autocarter.network import Connection, Line, Network, Station
from autocarter.style import Style
from autocarter.vector import Vector

with open("./stops.json") as f:
    stops = json.load(f)
with open("./services.json") as f:
    services = json.load(f)

n = Network()

stations = {}
for stop_id, stop_json in stops.items():
    station = n.add_station(
        Station(
            id=stop_id,
            name=stop_id + " " + stop_json[2].replace("&", "&amp;"),
            coordinates=Vector(stop_json[0], -stop_json[1]),
        )
    )
    stations.setdefault(stop_id[:-1], []).append(station)

for line_id, line_json in services.items():
    colour = (
        "#" + random.choice("0123456789abcdef") + random.choice("0123456789abcdef") + random.choice("0123456789abcdef")
    )
    for i, route in enumerate(line_json["routes"]):
        line = n.add_line(Line(id=line_id + "_" + str(i), name=line_id, colour=Colour.solid(colour)))
        if route[0] == route[-1]:
            n.stations[route[0]].adjacent_stations[line.id] = [[route[1], route[-2]], []]
        for s1_id, s2_id in itertools.pairwise(route):
            n.connect(n.stations[s1_id], n.stations[s2_id], line)

for stn_list in stations.values():
    for stn1, stn2 in itertools.combinations(stn_list, 2):
        n.connect(stn1, stn2, Connection())

n.finalise()

s = Drawer(n, Style(scale=75000.0, station_dots=True)).draw()
with open("./out.svg", "w") as f:
    f.write(str(s))
