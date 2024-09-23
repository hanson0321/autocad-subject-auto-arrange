import gurobipy as gp
from gurobipy import GRB
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib
from tools import get_feasible_area
import shelf_arrange
from tools import coordinate_flipping as flip
from tools import get_feasible_area
from dxf_tools import dxf_manipulation
import re

def shelf_opt(shelf_area, unusable_gridcell1, counter_placement, door_side, shelf_params, priority_shelves, gap_between_shelves):
    x, y = shelf_area['x'], shelf_area['y']
    max_width = int(shelf_area['w'])
    max_height = int(shelf_area['h'])
    if counter_placement == 'west':
        shelf_placement= shelf_arrange.layout_with_numeric_value(shelf_params, priority_shelves, max_width, max_height, gap_between_shelves)
        if door_side =='north':
            shelf_placement = flip.horizontal(max_height, shelf_placement)
    elif counter_placement == 'east':
        shelf_placement = shelf_arrange.layout_with_numeric_value(shelf_params, priority_shelves, max_width, max_height, gap_between_shelves)
        shelf_placement = flip.vertical(max_width, shelf_placement)
        if door_side =='south':
            shelf_placement = flip.horizontal(max_height, shelf_placement)
    elif counter_placement == 'north':
        shelf_placement = shelf_arrange.layout_with_numeric_value(shelf_params,priority_shelves, max_width, max_height, gap_between_shelves)
        shelf_placement = flip.cw(max_height, max_width, shelf_placement)
        if door_side =='east':
            shelf_placement = flip.vertical(max_height, shelf_placement)
    elif counter_placement == 'south':
        shelf_placement = shelf_arrange.layout_with_numeric_value(shelf_params, priority_shelves, max_width, max_height, gap_between_shelves)
        shelf_placement = flip.ccw(max_height, max_width, shelf_placement)
        if door_side =='east':
            shelf_placement = flip.horizontal(max_height, shelf_placement)
    num_shelf = len(shelf_placement)
    new_shelf_placement = {i: shelf_placement[key] for i, key in enumerate(shelf_placement.keys())}
    shelf_placement = new_shelf_placement

    for i in range(num_shelf):
        shelf_placement[i]['x'] = shelf_placement[i]['x']+x
        shelf_placement[i]['y'] = shelf_placement[i]['y']+y
    num_shelf = len(shelf_placement)
    

    for i in range(num_shelf):
        print(f"{shelf_placement[i]['name']} : x={shelf_placement[i]['x']}, y={shelf_placement[i]['y']}, w={shelf_placement[i]['w']}, h={shelf_placement[i]['h']}")

    unusable_gridcell2 = {}
    values = list(unusable_gridcell1.values())+list(shelf_placement.values())
    unusable_gridcell2 = {i: values[i] for i in range(len(values))}

    return shelf_placement, unusable_gridcell2