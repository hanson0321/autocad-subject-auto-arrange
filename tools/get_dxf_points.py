
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
    return points
