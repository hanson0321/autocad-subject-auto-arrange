import ezdxf
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

doc = ezdxf.readfile('/Users/lilianliao/Documents/研究所/Lab/Layout Generation/data/Test_Before.dxf')
msp = doc.modelspace()
points = []
for e in msp:
    if  e.dxftype() == "LWPOLYLINE":
        df = pd.DataFrame(e.get_points('xy'))
        points.append(e.get_points('xy'))
    elif e.dxftype() == 'LINE':
        start = e.dxf.start
        end = e.dxf.end
        points.append((start.x, start.y))
        points.append((end.x, end.y))
print(points)
