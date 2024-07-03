import json

import vector

from autocarter.drawer import Drawer, Style
from autocarter.network import Line, Network, Station

with open("./data.json") as f:
    data = json.load(f)["rail"]
n = Network()
company_uuid, company_json = next((k, v) for k, v in data["company"].items() if v["name"] == "MRT")

col = {
    "A": "#00FFFF",
    "B": "#EEDB95",
    "C": "#5E5E5E",
    "D": "#9437FF",
    "E": "#10D20F",
    "F": "#0096FF",
    # "G": "#0ff",
    "H": "#5B7F00",
    "I": "#FF40FF",
    "J": "#4C250D",
    # "K": "#0ff",
    "L": "#9B95BC",
    "M": "#FF8000",
    "N": "#0433FF",
    "O": "#021987",
    "P": "#008E00",
    # "Q": "#0ff",
    "R": "#FE2E9A",
    "S": "#FFFA28",
    "T": "#915001",
    "U": "#2B2C35",
    "V": "#FF8AD8",
    "W": "#FF0000",
    "X": "#000000",
    "XM": "#000000",
    # "Y": "#0ff",
    "Z": "#EEEEEE",
}

for line_uuid in company_json["lines"]:
    line_json = data["line"][line_uuid]
    colour = col.get(line_json["code"], "#888")
    n.add_line(Line(id=line_uuid, name=line_json["name"].removeprefix("MRT ").removesuffix(" Line"), colour=colour))

for station_uuid in company_json["stations"]:
    station_json = data["station"][station_uuid]
    if station_json["world"] == "Old" or not station_json["connections"]:
        continue
    coordinates = station_json["coordinates"] or [0, 0]
    n.add_station(
        Station(
            id=station_uuid,
            name=(" ".join(station_json["codes"]) + " " + (station_json["name"] or "")),
            coordinates=vector.obj(x=coordinates[0], y=coordinates[1]),
        )
    )

visited_stations = []
for station_uuid in company_json["stations"]:
    if station_uuid not in n.stations:
        continue
    station_json = data["station"][station_uuid]
    for conn_station_uuid, connections in station_json["connections"].items():
        if conn_station_uuid in visited_stations:
            continue
        for connection in connections:
            n.connect(n.stations[station_uuid], n.stations[conn_station_uuid], n.lines[connection["line"]])
    visited_stations.append(station_uuid)

n.finalise()

s = Drawer(n, Style(scale=0.05)).draw()
with open("./out.svg", "w") as f:
    f.write(str(s))
