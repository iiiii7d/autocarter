import vector

from autocarter.drawer import Drawer
from autocarter.network import Network, Station, Line

n = Network()

a = Station(name="A", coordinates=vector.obj(x=10, y=10))
b = Station(name="B", coordinates=vector.obj(x=20, y=20))
line = Line(colour="#ff0000", name="Line")
n.add_station(a)
n.add_station(b)
n.add_line(line)
n.connect(a, b, line)

s = Drawer(n).draw()
with open("out.svg", "w") as f:
    f.write(str(s))
