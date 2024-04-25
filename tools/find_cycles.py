import networkx as nx
from shapely.geometry import Polygon, LineString, Point
from itertools import combinations
from tools import json_save as js
from tools import plot
from tools import get_dxf_points as get_points

def add_edges_to_graph(graph, edges):
    for start, end in edges:
        graph.add_edge(start, end)

def find_cycle_edges(graph):
    # Find cycles in the graph and then create a list of edges for each cycle
    cycles = list(nx.cycle_basis(graph))
    cycle_edges = []
    for cycle in cycles:
        # Make sure to form a loop by adding the first node at the end
        cycle.append(cycle[0])
        cycle_edge_list = []
        for i in range(len(cycle) - 1):
            cycle_edge_list.append([cycle[i], cycle[i+1]])
        cycle_edges.append(cycle_edge_list)
    return cycle_edges

def split_edges_into_segments(edges):
    print("Splitting into no-tuning point segments")
    segmented_edges = []
    for edge in edges:
        # Create pairs of consecutive vertices
        for i in range(len(edge) - 1):
            segmented_edges.append([edge[i], edge[i + 1]])
    return segmented_edges

def check_point_on_segment(point, segment):
    """Check if the point lies on the segment."""
    point = Point(point)
    return point.distance(segment) == 0

def segment_line(line, points):
    """Slices a line at multiple points, returning the resulting line segments."""
    # Remove duplicate points and sort points by their distance along the line
    unique_points = list(set(points))
    sorted_points = sorted(unique_points, key=lambda p: line.project(Point(p)))
    # Include original endpoints of the line
    all_points = [line.coords[0]] + sorted_points + [line.coords[-1]]
    # Generate segments between these points
    segments = [LineString(all_points[i:i+2]) for i in range(len(all_points) - 1) if all_points[i] != all_points[i+1]]
    return segments

def find_intersections_and_slice(edges):
    print("Slicing into smallest segments")
    lines = [(LineString([start, end]), start, end) for start, end in edges]
    intersection_points = {line: [] for line, _, _ in lines}
    # Identify intersection points
    for line, start, end in lines:
        start_point = Point(start)
        end_point = Point(end)
        for other_line, _, _ in lines:
            if other_line != line:
                if check_point_on_segment(start, other_line) and start not in intersection_points[other_line]:
                    intersection_points[other_line].append(start)
                if check_point_on_segment(end, other_line) and end not in intersection_points[other_line]:
                    intersection_points[other_line].append(end)
    # Slice each line into segments
    sliced_segments = []
    for line, points in intersection_points.items():
        segments = segment_line(line, points)
        sliced_segments.extend(segments)
    return sliced_segments

def find(edges):
    print("Finding close cycles")
    # Transform edges to simple segments
    segmented_edges = split_edges_into_segments(edges)
    edges = segmented_edges
    final_segments = find_intersections_and_slice(edges)
    # Outputting the segments as a list of tuples
    final_list = [list(segment.coords) for segment in final_segments]
    sliced_seg = []
    for segment in final_list:
        sliced_seg.append(segment)
    # Build the graph
    G = nx.Graph()
    add_edges_to_graph(G, sliced_seg)
    cycle_list_for_visualization = []
    cycle_list = []
    # Output the cycles found
    cycle_edges = find_cycle_edges(G)
    for cycle in cycle_edges:
        cycle_list_for_visualization.extend(cycle)
        cycle_list.append(cycle)
    return  cycle_list

if __name__ =='__main__':
    plot.plot(find(get_points.get_points('/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/Test_Before.dxf')))