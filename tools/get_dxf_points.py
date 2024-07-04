import ezdxf
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt


def get_points(file_path):
    print("Getting points from dxf")
    doc = ezdxf.readfile(file_path)
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
    return points

if __name__ == '__main__':
    print(get_points('/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/Test_Before.dxf'))
