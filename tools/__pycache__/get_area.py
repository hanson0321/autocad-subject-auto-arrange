import networkx as nx
from shapely.geometry import Polygon, LineString, Point
from itertools import combinations
from tools import json_save as js
from tools import plot
from tools import find_cycles as find
from copy import deepcopy
import ezdxf
import pandas as pd
import matplotlib.pyplot as plt
from tools import get_dxf_points as dxfpoints
from tools import share_edges_merge as share


def calculate_area(vertices):
    print("Calculating")
    # Construct a polygon and calculate its area
    polygon = Polygon(vertices)
    return polygon.area

def largest_enclosed_area(cycle_list):
    # Calculate the area of each cycle
    areas = []
    #print(f'cycle are:{find.find(edges)}')
    print('Finding largest area')
    for cycle in cycle_list:
        cycle_copy = deepcopy(cycle)
        print("Forming closed path")
        area = calculate_area(form_closed_path(cycle))
        areas.append((area,cycle_copy))
 # Store area and the cycle excluding the last repeated point
    # Find the cycle with the largest area
    if areas:
        largest = max(areas, key=lambda x: x[0])
        largest_area, largest_cycle = largest
        # Find the edges that form this cycle
        largest_edges = [(largest_cycle[i], largest_cycle[i+1]) for i in range(len(largest_cycle) - 1)]
        print(largest_edges)
        js.json_save(largest_edges,'largest_area')
        return largest_area, largest_cycle, largest_edges
    else:
        return 0, [], []
    
def form_closed_path(edges):
    if not edges:
        return tuple()
    
    # Start with the first edge
    path = list(edges[0])
    edges.remove(edges[0])
    
    # Follow edges to form the path
    while edges:
        for i, edge in enumerate(edges):
            # Check if the last point in path matches the first point in an edge
            if path[-1] == edge[0]:
                path.append(edge[1])  # Append the next point
                edges.pop(i)          # Remove used edge
                break
            # Check if the last point in path matches the last point in an edge (reverse connection)
            elif path[-1] == edge[1]:
                path.append(edge[0])  # Append the next point, but reversed
                edges.pop(i)          # Remove used edge
                break
    return path

# Define edges based on the earlier segmentation or any new definition
'''
edges = [
    [(3, 4), (4, 9)],
    [(4, 9), (11, 9)],
    [(10, 9), (8, 4)],
    [(8, 4), (3, 4)],
    [(5,4), (5,9)],
    [(5,6),(7,9)],
    [(6,5),(6,6)],
    [(6,6),(7,6)],
    [(7,6),(7,5)],
    [(7,5),(6,5)]
]
'''
#edges = dxfpoints.get_points('/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/Test_Before.dxf')
cycle_list = js.json_open('/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/cycle_list_data.json')
#cycle_list = find.find(edges)


# Get the largest enclosed area, its vertices, and its edges
largest_area, vertices, edges_forming_area = largest_enclosed_area(cycle_list)
print(f"Largest Area: {largest_area}")
print(f"Edges forming the largest area: {edges_forming_area}")
plot.plot(edges_forming_area)

