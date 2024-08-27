import matplotlib.pyplot as plt
from shapely.geometry import Polygon, box, LineString
import gurobipy as gp
from gurobipy import GRB
import time
import matplotlib.patches as patches
import matplotlib
from tools import get_feasible_area
from tools import KPtest
from tools import coordinate_flipping as flip
from tools import get_feasible_area
from dxf_tools import dxf_manipulation
from shapely import affinity
import math
import re
from shapely.ops import unary_union

def create_preplaced_polygons(unusable_gridcells):
    return [box(cell['x'], cell['y'], cell['x'] + cell['w'], cell['y'] + cell['h']) 
            for cell in unusable_gridcells.values()]

def calculate_edge_lengths(edges):
    lengths = {}
    for edge in edges:
        lengths[edge] = edge.length
    return lengths

def find_closest_segment(specified_segment, edges):
    closest_segment = None
    min_distance = float('inf')
    x_s1, y_s1 = specified_segment.xy[0]
    x_s2, y_s2 = specified_segment.xy[1]
    specified_seg_orientation = 0
    if x_s1 == x_s2:
        specified_seg_orientation = 1
    else:
        pass
    for edge in edges:
        edge_orientation = 0
        if edge != specified_segment:
            distance = specified_segment.distance(edge)
            if edge.length >= 598:
                x1, y1 = edge.coords[0]
                x2, y2 = edge.coords[1]
                if x1 == x2:  # Vertical edge
                    edge_orientation = 1
                else:
                    pass
                if specified_seg_orientation != edge_orientation:
                    if distance < min_distance:
                        min_distance = distance
                        closest_segment = edge
    return closest_segment, edge_orientation

def place_counter_along_wall(room_polygon, rectangles, preplaced_polygons, specified_segment, min_x, max_x, min_y, max_y):
    # Extract the edges of the polygon
    edges = [LineString([room_polygon.exterior.coords[i], room_polygon.exterior.coords[i+1]])
             for i in range(len(room_polygon.exterior.coords) - 1)]

    # Calculate lengths of each edge
    edge_lengths = calculate_edge_lengths(edges)
    
    # Sort edges by length in descending order
    sorted_edges = sorted(edge_lengths.keys(), key=lambda e: edge_lengths[e], reverse=True)
    
    # Initialize available segments for each edge
    available_segments = {edge: [edge] for edge in sorted_edges}
    
    # Union of pre-placed polygons
    preplaced_union = unary_union(preplaced_polygons)
    
    # Find the closest segment to the specified segment
    closest_segment, edge_orientation = find_closest_segment(specified_segment, edges)
    
    placements = []
    for rect_width, rect_height in rectangles:
        placed = False
        for edge in [closest_segment] + sorted_edges:
            long_side = max(rect_width, rect_height)
            short_side = min(rect_width, rect_height)
            
            new_segments = []
            for segment in available_segments[edge]:
                x1, y1 = segment.coords[0]
                x2, y2 = segment.coords[1]
                
                if x1 == x2:  # Vertical edge
                    if long_side <= abs(y2 - y1):
                        # Try to place the rectangle along the vertical segment
                        min_y = min(y1, y2)
                        max_y = max(y1, y2)
                        for start_y in range(int(min_y), int(max_y - long_side) + 1):
                            rect = box(x1 - short_side, start_y, x1, start_y + long_side)
                            if room_polygon.contains(rect) and not rect.intersects(preplaced_union) and all(not rect.intersects(p) for p in placements):
                                placements.append(rect)
                                placed = True
                                new_segments = [
                                    LineString([(x1, min_y), (x1, start_y)]),
                                    LineString([(x1, start_y + long_side), (x1, max_y)])
                                ]
                                break
                        if placed:
                            break
                elif y1 == y2:  # Horizontal edge
                    if long_side <= abs(x2 - x1):
                        # Try to place the rectangle along the horizontal segment
                        min_x = min(x1, x2)
                        max_x = max(x1, x2)
                        for start_x in range(int(min_x), int(max_x - long_side) + 1):
                            rect = box(start_x, y1, start_x + long_side, y1 + short_side)
                            if room_polygon.contains(rect) and not rect.intersects(preplaced_union) and all(not rect.intersects(p) for p in placements):
                                placements.append(rect)
                                placed = True
                                new_segments = [
                                    LineString([(min_x, y1), (start_x, y1)]),
                                    LineString([(start_x + long_side, y1), (max_x, y1)])
                                ]
                                break
                        if placed:
                            break
            if placed:
                # Update available segments for the current edge
                available_segments[edge] = [seg for seg in new_segments if seg.length > 0]
                break
        if not placed:
            print(f"Rectangle {rect_width}x{rect_height} could not be placed.")

    if edge_orientation == 1:
        counter_orientation = 0
    else:
        counter_orientation = 1



    return placements, counter_orientation, available_segments

def counter_placements(room_polygon, obj_params, counter_space, lineup_space, specified_segment, preplaced, min_x, max_x, min_y, max_y):
    rectangles = []
    for id , object in obj_params.items():
        print(object['name'])
        if object['name'] == '後櫃檯':
            w1 = max(object['w_h'])
            h1 = min(object['w_h'])
        elif object['name'] == '前櫃檯':
            w2 = max(object['w_h'])
            h2 = min(object['w_h'])
        else:
            pass
    rectangles.append((w1, h1 + h2 + counter_space + lineup_space))

    # Create saved space for door entry
    preplaced_polygons = create_preplaced_polygons(preplaced)

    placements, counter_orientation, available_segments = place_counter_along_wall(room_polygon, rectangles, preplaced_polygons, specified_segment, min_x, max_x, min_y, max_y)

    # Extract the bounds of the polygon (minx, miny, maxx, maxy)
    minx, miny, maxx, maxy = placements[0].bounds

    # Calculate width and height
    width = maxx - minx
    height = maxy - miny

    # Create the dictionary
    counter_area = {
        'x': minx,
        'y': miny,
        'w': width,
        'h': height
    }

    # Find middle point of the object
    x1, y1 = specified_segment.coords[0]
    x2, y2 = specified_segment.coords[1]
    if counter_orientation == 1:
        middle_point = counter_area['x']+counter_area['w']/2
        d1 = middle_point - min_x
        d2 = max_x - middle_point
        dd1 = y1 -min_y
        dd2 = max_y - y1
        if d1 > d2:
            counter_placement = 'east'
        else:
            counter_placement = 'west'
        if dd1 > dd2:
            door_placement = 'north'
        else:
            door_placement = 'south'
    else:
        middle_point = counter_area['y']+counter_area['h']/2
        d1 = middle_point - min_y
        d2 = max_y - middle_point
        dd1 = x1 -min_x
        dd2 = max_x - x1
        if d1 > d2:
            counter_placement = 'south'
        else:
            counter_placement = 'north' 
        if dd1 > dd2:
            door_placement = 'east'
        else:
            door_placement = 'west'


    counter_result = {}
    if counter_placement =='east' and door_placement == 'north':
        counter_result.update({0:{'x':counter_area['x']+counter_area['w']-h1, 'y':counter_area['y'], 'w':h1, 'h':w1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+lineup_space, 'y':counter_area['y']+(w1-w2), 'w':h2, 'h':w2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x'], 'y':counter_area['y']+(w1-w2), 'w':lineup_space, 'h':w2}})
        unusable_gridcell0.update({3:{'x':counter_area['x']+lineup_space+h2, 'y':counter_area['y'], 'w':counter_space, 'h':w1}})
    elif counter_placement =='east' and door_placement == 'south':
        counter_result.update({0:{'x':counter_area['x']+counter_area['w']-h1, 'y':counter_area['y'], 'w':h1, 'h':w1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+lineup_space, 'y':counter_area['y'], 'w':h2, 'h':w2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x'], 'y':counter_area['y'], 'w':lineup_space, 'h':w2}})
        unusable_gridcell0.update({3:{'x':counter_area['x']+lineup_space+h2, 'y':counter_area['y'], 'w':counter_space, 'h':w1}})
    elif counter_placement =='west' and door_placement == 'north':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y'], 'w':h1, 'h':w1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+h1+counter_space, 'y':counter_area['y']+(w1-w2), 'w':h2, 'h':w2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x']+h1+counter_space+h2, 'y':counter_area['y']+(w1-w2), 'w':lineup_space, 'h':w2}})
        unusable_gridcell0.update({3:{'x':counter_area['x']+h1, 'y':counter_area['y'], 'w':counter_space, 'h':w1}})
    elif counter_placement =='west' and door_placement == 'south':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y'], 'w':h1, 'h':w1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+h1+counter_space, 'y':counter_area['y'], 'w':h2, 'h':w2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x']+counter_area['w']-lineup_space, 'y':counter_area['y'], 'w':lineup_space, 'h':w2}})
        unusable_gridcell0.update({3:{'x':counter_area['x']+h1, 'y':counter_area['y'], 'w':counter_space, 'h':w1}})
    
    elif counter_placement =='north' and door_placement == 'west':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y']+counter_area['h']-h1, 'w':w1, 'h':h1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x'], 'y':counter_area['y']+lineup_space, 'w':w2, 'h':h2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x'], 'y':counter_area['y'], 'w':w2, 'h':lineup_space}})
        unusable_gridcell0.update({3:{'x':counter_area['x'], 'y':counter_area['y']+lineup_space+h2, 'w':w1, 'h':counter_space}})
    elif counter_placement =='north' and door_placement == 'east':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y']+counter_area['h']-h1, 'w':w1, 'h':h1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+(w1-w2), 'y':counter_area['y']+lineup_space, 'w':w2, 'h':h2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x']+(w1-w2), 'y':counter_area['y'], 'w':w2, 'h':lineup_space}})
        unusable_gridcell0.update({3:{'x':counter_area['x'], 'y':counter_area['y']+lineup_space+h2, 'w':w1, 'h':counter_space}})
    elif counter_placement =='south' and door_placement == 'west':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y'], 'w':w1, 'h':h1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x'], 'y':counter_area['y']+h1+counter_space, 'w':w2, 'h':h2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x'], 'y':counter_area['y']+counter_area['h']-lineup_space, 'w':w2, 'h':lineup_space}})
        unusable_gridcell0.update({3:{'x':counter_area['x'], 'y':counter_area['y']+h1, 'w':w1, 'h':counter_space}})
    elif counter_placement =='south' and door_placement == 'east':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y'], 'w':w1, 'h':h1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+(w1-w2), 'y':counter_area['y']+h1+counter_space, 'w':w2, 'h':h2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x']+(w1-w2), 'y':counter_area['y']+counter_area['h']-lineup_space, 'w':w2, 'h':lineup_space}})
        unusable_gridcell0.update({3:{'x':counter_area['x'], 'y':counter_area['y']+h1, 'w':w1, 'h':counter_space}})
    values = list(unusable_gridcell0.values())+list(preplaced.values())
    unusable_gridcell0 = {}
    unusable_gridcell0 = {i: values[i] for i in range(len(values))}
    return  counter_result, counter_placement, unusable_gridcell0, available_segments

if __name__ == '__main__':
    doc ='/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/revise.dxf'
    unusable_gridcell, min_x, max_x, min_y, max_y, poly_feasible = get_feasible_area.feasible_area(doc)

    SPACE_WIDTH,SPACE_HEIGHT= max_x-min_x+1, max_y-min_y+1
    AISLE_SPACE = 100
    COUNTER_SPACING = 110
    OPENDOOR_SPACING = 110
    LINEUP_SPACING = 160
    
    #Define the parameters and variables
    obj_params = {
        0: {'group':2,'w_h': [SPACE_WIDTH,SPACE_HEIGHT], 'fixed_wall': 'none', 'name':'貨架區'},
        1: {'group':0,'w_h': [465,66], 'fixed_wall': 'none', 'name':'前櫃檯'},
        2: {'group':0,'w_h': [598,66], 'fixed_wall': 'any', 'name':'後櫃檯'},
        3: {'group':1,'w_h': [365,270], 'fixed_wall': 'any', 'name':'WI'}, 
        4: {'group':2,'w_h': [90,66], 'fixed_wall': 'none', 'name':'雙溫櫃'},
        5: {'group':2,'w_h': [90,66], 'fixed_wall': 'none', 'name':'單溫櫃'},
        6: {'group':2,'w_h': [90,66], 'fixed_wall': 'none', 'name':'OC'},
        7: {'group':1,'w_h': [310,225], 'fixed_wall': 'any', 'name':'RI'},
        8: {'group':1,'w_h': [95,59], 'fixed_wall': 'any', 'name':'EC'},
        9: {'group':1,'w_h': [190,90], 'fixed_wall': 'any', 'name':'子母櫃'},
        10: {'group':1,'w_h': [100,85], 'fixed_wall': 'any', 'name':'ATM'},
        11: {'group':1,'w_h': [83,64], 'fixed_wall': 'any', 'name':'影印'},
        12: {'group':1,'w_h': [80,55], 'fixed_wall': 'any', 'name':'KIOSK'}
    }

    unusable_gridcell = {}
    # Define the specified segment (e.g., the first edge of the polygon)
    DOOR_PLACEMENT = LineString([(1031,150), (1409,150)])
    # Space for door entry
    DOOR_ENTRY= {
        0: {'x': 1031, 'y': 150, 'w': 378, 'h': 200}
    }

    counter_result, counter_placement, unusable_gridcell1, available_segments = counter_placements(poly_feasible, obj_params, COUNTER_SPACING, LINEUP_SPACING, DOOR_PLACEMENT, DOOR_ENTRY, min_x, max_x, min_y, max_y)
    # Plotting
    fig, ax = plt.subplots()

    # Plot the room polygon
    x, y = poly_feasible.exterior.xy
    ax.plot(x, y, color='blue', linewidth=2, label='Room')

    # Plot the pre-placed rectangles
    for cell in unusable_gridcell1.values():
        rect = box(cell['x'], cell['y'], cell['x'] + cell['w'], cell['y'] + cell['h'])
        x, y = rect.exterior.xy
        ax.plot(x, y, color='grey', linewidth=2, linestyle='--', label='Pre-placed')

    # Plot the placed rectangles
    for rect in counter_result.values():
        rect = box(rect['x'], rect['y'], rect['x'] + rect['w'], rect['y'] + rect['h'])
        x, y = rect.exterior.xy
        ax.plot(x, y, color='red', linewidth=2)

    # Highlight the specified and closest segments
    x, y = DOOR_PLACEMENT.xy
    ax.plot(x, y, color='green', linewidth=2, linestyle='--', label='Specified Segment')

    ax.set_aspect('equal')
    plt.legend()
    plt.show()
