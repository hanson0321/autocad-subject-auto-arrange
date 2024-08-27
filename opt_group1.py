import matplotlib.pyplot as plt
from shapely.geometry import Polygon, box, LineString
import gurobipy as gp
from gurobipy import GRB
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib
from tools import get_feasible_area
from tools import KPtest
from tools import coordinate_flipping as flip
from tools import get_feasible_area
from dxf_tools import dxf_manipulation
from shapely import affinity
import random
import re
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union
import opt_group0


def create_preplaced_polygons(unusable_gridcell0):
    return [box(cell['x'], cell['y'], cell['x'] + cell['w'], cell['y'] + cell['h']) 
            for cell in unusable_gridcell0.values()]

def calculate_edge_lengths(edges):
    lengths = {}
    for edge in edges:
        lengths[edge] = edge.length
    return lengths

def place_object_along_wall(obj_params, edges, rectangles, preplaced_polygons, room_polygon, space_min_x, space_min_y, space_max_x, space_max_y, door_opening_space, unusable_gridcell, unusable_gridcell0):
    # random.shuffle(rectangles)
    rectangles = sorted(rectangles, key=lambda x: max(x), reverse=True)
    print(rectangles)
    # Calculate lengths of each edge
    edge_lengths = calculate_edge_lengths(edges)
    print(edge_lengths)
    # Sort edges by length in descending order
    sorted_edges = sorted(edge_lengths.keys(), key=lambda e: edge_lengths[e], reverse=True)

    # Initialize available segments for each edge
    available_segments = {edge: [edge] for edge in sorted_edges}
    # Union of pre-placed polygons
    preplaced_union = unary_union(preplaced_polygons)
    placements = []
    placement_with_door = []
    len_object = 0
    for edge in available_segments:
        print(f'Placing on {edge}')
        len_object = 0
        print(f'Remaining rectangles to place: {rectangles}')
        while (len_object/edge.length)<=0.6:
            new_segments = []
            placed_rect = []
            x1, y1 = edge.coords[0]
            x2, y2 = edge.coords[1]
            
            if x1 == x2:  # Vertical edge
                print('Vertical')
                for rect_width, rect_height in rectangles:
                    placed = False
                    print(f'Trying to place rectangle: {[rect_width, rect_height]}...')
                    long_side = max(rect_width, rect_height)
                    short_side = min(rect_width, rect_height)
                    if long_side <= abs(y2 - y1):
                        # Try to place the rectangle along the vertical segment
                        min_y = min(y1, y2)
                        max_y = max(y1, y2)
                        if x1 < (space_min_x+space_max_x)/2:
                            start = random.randint(int(min_y), int(max_y - long_side) + 1)
                            for i in range(int(min_y), int(max_y - long_side) + 1):
                                start_y = (start + i) % (int(max_y - long_side) + 1)
                                rect = box(x1, start_y, x1 + short_side, start_y + long_side)
                                rect_with_door = box(x1, start_y, x1 + short_side + door_opening_space, start_y + long_side)
                                if room_polygon.contains(rect_with_door) and not rect_with_door.intersects(preplaced_union) and all(not rect_with_door.intersects(p) for p in placement_with_door):
                                    placements.append(rect)
                                    placement_with_door.append(rect_with_door)
                                    placed = True
                                    new_segments = [
                                        LineString([(x1, min_y), (x1, start_y)]),
                                        LineString([(x1, start_y + long_side), (x1, max_y)])
                                    ]
                                    break
                        else:
                            start = random.randint(int(min_y), int(max_y - long_side) + 1)
                            for i in range(int(min_y), int(max_y - long_side) + 1):
                                start_y = (start + i) % (int(max_y - long_side) + 1)
                                rect = box(x1 - short_side, start_y, x1, start_y + long_side)
                                rect_with_door = box(x1 - (short_side+door_opening_space), start_y, x1, start_y + long_side)
                                if room_polygon.contains(rect_with_door) and not rect_with_door.intersects(preplaced_union) and all(not rect_with_door.intersects(p) for p in placement_with_door):
                                    placements.append(rect)
                                    placement_with_door.append(rect_with_door)
                                    placed = True
                                    new_segments = [
                                        LineString([(x1, min_y), (x1, start_y)]),
                                        LineString([(x1, start_y + long_side), (x1, max_y)])
                                    ]
                                    break
                        if placed:
                            print('Rectangle plcaed!')
                            available_segments[edge] = [seg for seg in new_segments if seg.length > 0]
                            placed_rect.append([rect_width, rect_height])
                            rectangles = [i for i in rectangles if i not in placed_rect]
                            break
                        if not placed:
                            rectangles = [i for i in rectangles if i not in placed_rect]
                            print(f'New list: {rectangles}')
                            print('Moving on to the next rectangle...')
                            break

            elif y1 == y2:  # Horizontal edge
                print('Horizontal')
                for rect_width, rect_height in rectangles:
                    print(f'Trying to place rectangle: {[rect_width, rect_height]}...')
                    placed = False
                    long_side = max(rect_width, rect_height)
                    short_side = min(rect_width, rect_height)
                    if long_side <= abs(x2 - x1):
                        # Try to place the rectangle along the horizontal segment
                        min_x = min(x1, x2)
                        max_x = max(x1, x2)
                        if y1 < (space_min_y+space_max_y)/2:
                            start = random.randint(int(min_x), int(max_x - long_side) + 1)
                            for i in range(int(min_x), int(max_x - long_side) + 1):
                                start_x = (start + i) % (int(max_x - long_side) + 1)
                                rect = box(start_x, y1, start_x + long_side, y1 + short_side)
                                rect_with_door = box(start_x, y1, start_x + long_side, y1 + short_side+door_opening_space)
                                if room_polygon.contains(rect_with_door) and not rect_with_door.intersects(preplaced_union) and all(not rect_with_door.intersects(p) for p in placement_with_door):
                                    placements.append(rect)
                                    placement_with_door.append(rect_with_door)
                                    placed = True
                                    new_segments = [
                                        LineString([(min_x, y1), (start_x, y1)]),
                                        LineString([(start_x + long_side, y1), (max_x, y1)])
                                    ]
                                    break
                        else:
                            start = random.randint(int(min_x), int(max_x - long_side) + 1)
                            for i in range(int(min_x), int(max_x - long_side) + 1):
                                start_x = (start + i) % (int(max_x - long_side) + 1)
                                rect = box(start_x, y1-short_side, start_x + long_side, y1)
                                rect_with_door = box(start_x, y1-(short_side+door_opening_space), start_x + long_side, y1)
                                if room_polygon.contains(rect_with_door) and not rect_with_door.intersects(preplaced_union) and all(not rect_with_door.intersects(p) for p in placement_with_door):
                                    placements.append(rect)
                                    placement_with_door.append(rect_with_door)
                                    placed = True
                                    new_segments = [
                                        LineString([(min_x, y1), (start_x, y1)]),
                                        LineString([(start_x + long_side, y1), (max_x, y1)])
                                    ]
                                    break                        
                        if placed:
                            print('Rectangle plcaed!')
                            available_segments[edge] = [seg for seg in new_segments if seg.length > 0]
                            placed_rect.append([rect_width, rect_height])
                            rectangles = [i for i in rectangles if i not in placed_rect]
                            break
                        if not placed:
                            rectangles = [i for i in rectangles if i not in placed_rect]
                            print(f'New list: {rectangles}')
                            print('Moving on to the next rectangle...')
                            break
            
            len_object+=long_side
            print(len_object)
            print(f'Placed rectangls: {placed_rect}')
            if not rectangles:
                rectangles = [i for i in rectangles if i not in placed_rect]
                print(f'New list: {rectangles}')
                break
            
        if rectangles:
            print('Moving on to the next edge...')
            continue
        if not rectangles:
            print('All rectangles placed!')
            break
    placement_with_door = create_dict_from_polygons(placement_with_door, obj_params)
    unusable_gridcell1 = {}
    values = list(unusable_gridcell.values()) + list(unusable_gridcell0.values())+list(placement_with_door.values())
    unusable_gridcell1 = {i: values[i] for i in range(len(values))}
    print(unusable_gridcell1)
    placements_dict = create_dict_from_polygons(placements, obj_params)
    return placements, placements_dict, unusable_gridcell1


# Function to create dictionary from list of polygons
def create_dict_from_polygons(polygons, obj_params):
    rect_dict = {}
    for i, poly in enumerate(polygons):
        if poly == 0:
            break
        min_x, min_y, max_x, max_y = poly.bounds
        rect_dict[i] = {
            'x': min_x,
            'y': min_y,
            'w': max_x - min_x,
            'h': max_y - min_y
        }

    for id, object in rect_dict.items():
        for _, obj in obj_params.items():
            if max(object['w'],object['h']) == max(obj['w_h']) and min(object['w'],object['h'])==min(obj['w_h']):
                rect_dict[id]['name'] = obj['name']
    return rect_dict





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

    # Define the specified segment (e.g., the first edge of the polygon)
    DOOR_PLACEMENT = LineString([(1031,150), (1409,150)])
    # Space for door entry
    DOOR_ENTRY= {
        0: {'x': 1031, 'y': 150, 'w': 378, 'h': 200}
    }
    
    # List of rectangles with their dimensions (width, height)
    rectangles = [[365,270], [310,225], [95,59], [190,90], [100,85], [83,64], [80,55]]
    # Create pre-placed polygons
    counter_result, counter_placement, unusable_gridcell0, available_segments = opt_group0.counter_placements(poly_feasible, obj_params, COUNTER_SPACING, LINEUP_SPACING, DOOR_PLACEMENT, DOOR_ENTRY, min_x, max_x, min_y, max_y)
    preplaced_polygons = create_preplaced_polygons(unusable_gridcell0)
    placements_polygon, placements, unusable_gridcell1 = place_object_along_wall(obj_params, available_segments, rectangles, preplaced_polygons,poly_feasible, min_x, min_y, max_x, max_y, OPENDOOR_SPACING, unusable_gridcell, unusable_gridcell0)
    # Convert list of polygons to dictionary
    result = create_dict_from_polygons(placements,obj_params)
    print(result)

    # Plotting
    fig, ax = plt.subplots()

    # Plot the room polygon
    x, y = poly_feasible.exterior.xy
    ax.plot(x, y, color='blue', linewidth=2, label='Room')

    # Plot the pre-placed rectangles
    for cell in unusable_gridcell0.values():
        rect = box(cell['x'], cell['y'], cell['x'] + cell['w'], cell['y'] + cell['h'])
        x, y = rect.exterior.xy
        ax.plot(x, y, color='grey', linewidth=2, linestyle='--', label='Pre-placed')

    # Plot the placed rectangles
    for rect in placements_polygon:
        x, y = rect.exterior.xy
        ax.plot(x, y, color='red', linewidth=2)

    ax.set_aspect('equal')
    plt.legend()
    plt.show()
