import json
import re

import vector

from autocarter.drawer import Drawer, Style
from autocarter.network import Line, Network, Station

with open("data.json") as f:
    data = json.load(f)["rail"]
n = Network()
company_uuid, company_json = next((k, v) for k, v in data["company"].items() if v["name"] == "nFLR")

col = {
    "1": "#c00",
    "2": "#ffa500",
    "3": "#fe0",
    "4": "#987654",
    "5": "#008000",
    "6": "#0c0",
    "7": "#0cc",
    "8": "#008b8b",
    "9": "#00c",
    "10": "",
    "11": "",
    "12": "",
    "13": "#555",
    "14": "#aaa",
    "15": "#000",
    "16": "#eee",
    "17": "#c2b280",
    "18": "#bb9955",
    "19": "#000080",
    "20": "#965f46",
    "21": "#8b3d2e",
    "22": "#a3501e",
    "23": "#bb8725",
    "24": "#3d291b",
    "N1": "#8c0",
    "N2": "#5cf",
    "N3": "#f5f",
    "N4": "#fc0",
    "AB": "",
}

for line_uuid in company_json["lines"]:
    line_json = data["line"][line_uuid]
    name = line_json["name"]
    if name.startswith("N") or name == "AB":
        colour = col[name]
    elif name.startswith("W"):
        colour = col[name[1:]]
    else:
        match = re.search(r"^(.)(\d+)(.*)$", line_json["name"])
        colour = col[match.group(2)]
    n.add_line(Line(id=line_uuid, name=line_json["name"], colour=colour))

for station_uuid in company_json["stations"]:
    station_json = data["station"][station_uuid]
    coordinates = station_json["coordinates"] or [0, 0]
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
    for conn_station_uuid, connections in station_json["connections"].items():
        if conn_station_uuid in visited_stations:
            continue
        for connection in connections:
            if n.lines[connection["line"]].name.startswith("W"):
                continue
            n.connect(n.stations[station_uuid], n.stations[conn_station_uuid], n.lines[connection["line"]])
    visited_stations.append(station_uuid)

n.finalise()

s = Drawer(n, Style(scale=0.03)).draw()
with open("out.svg", "w") as f:
    f.write(str(s))
