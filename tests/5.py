import json
import re

import vector

from autocarter.drawer import Drawer, Style
from autocarter.network import Line, Network, Station

with open("./data.json") as f:
    data = json.load(f)["rail"]
n = Network()
company_uuid, company_json = next((k, v) for k, v in data["company"].items() if v["name"] == "BluRail")

for line_uuid in company_json["lines"]:
    line_json = data["line"][line_uuid]
    name = line_json["name"]
    colour = (
        "#c01c22" if line_json["code"].endswith("X") else "#0a7ec3" if line_json["code"][-1].isdigit() else "#0c4a9e"
    )
    n.add_line(Line(id=line_uuid, name=line_json["code"], colour=colour))

for station_uuid in company_json["stations"]:
    station_json = data["station"][station_uuid]
    coordinates = station_json["coordinates"] or [0, 0]
    if coordinates == [0, 0]:
        print("No coords", station_json["name"])
    n.add_station(
        Station(
            id=station_uuid,
            name=station_json["name"].replace("&", "&amp;"),
            coordinates=vector.obj(x=coordinates[0], y=coordinates[1]),
        )
    )

visited_stations = []
for station_uuid in company_json["stations"]:
    station_json = data["station"][station_uuid]
    if not station_json["connections"]:
        print("No conns", station_json["name"])
    for conn_station_uuid, connections in station_json["connections"].items():
        if conn_station_uuid in visited_stations:
            continue
        for connection in connections:
            n.connect(
                n.stations[station_uuid],
                n.stations[conn_station_uuid],
                n.lines[connection["line"]],
            )
    visited_stations.append(station_uuid)

n.finalise()

s = Drawer(n, Style(scale=0.05)).draw()
with open("./out.svg", "w") as f:
    f.write(str(s))
