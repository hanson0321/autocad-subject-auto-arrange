#去除不是建物的雜訊，所有的線段都是最短線段
import ezdxf
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point
from tool import json_save as js
from tool import plot
from tool import find_cycles as find

def main(file_path):
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()
    points = []
    for e in msp:
        if  e.dxftype() == "LWPOLYLINE":
            df = pd.DataFrame(e.get_points('xy'))
            points.append(e.get_points('xy'))
    # Input: list of edges with multiple turning points
    edges = points
    results = find.find(edges)
    js.json_save(results,'preprocessed')
    return results

if __name__ == '__main__':
    plot.plot(main('/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/Test_Before.dxf'))
    


