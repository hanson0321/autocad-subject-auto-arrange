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
            points.append([(start.x, start.y),(end.x, end.y)])
    return points

# Input data
def get_rectangle(file_path):
    lines = get_points(file_path)
    # Flatten the list of lines to get all points
    all_points = [point for line in lines for point in line]

    # Initialize variables to store the desired points
    min_x_point = min(all_points, key=lambda point: point[0])
    max_x_point = max(all_points, key=lambda point: point[0])
    min_y_point = min(all_points, key=lambda point: point[1])
    max_y_point = max(all_points, key=lambda point: point[1])
    W = max_x_point[0]-min_x_point[0]
    H = max_y_point[1]-min_y_point[1]
    print("W = ", max_x_point[0]-min_x_point[0])
    print("H = ", max_y_point[1]-min_y_point[1])
    
    return W, H

if __name__ == '__main__':
    print(get_points('/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/result.dxf'))