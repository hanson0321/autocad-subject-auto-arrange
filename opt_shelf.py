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
import re

def shelf_opt(shelf_area, shelf_spec, shelf_height, counter_placement):
    x, y = shelf_area['x'], shelf_area['y']
    max_width = int(shelf_area['w'])
    max_height = int(shelf_area['h'])
    if counter_placement == 'west':
        shelf_placement = KPtest.knapsack_placement(max_width, max_height, shelf_spec, shelf_height)
        shelf_placement = KPtest.add_FF(shelf_placement,shelf_spec, max_width)
    elif counter_placement == 'east':
        shelf_placement = KPtest.knapsack_placement(max_width, max_height, shelf_spec, shelf_height)
        shelf_placement = KPtest.add_FF(shelf_placement,shelf_spec, max_width)
        shelf_placement = flip.vertical(max_width, shelf_placement)
    elif counter_placement == 'north':
        shelf_placement = KPtest.knapsack_placement(max_height, max_width, shelf_spec, shelf_height)
        shelf_placement = KPtest.add_FF(shelf_placement,shelf_spec, max_width)
        shelf_placement = flip.cw(max_height, max_width, shelf_placement)
    elif counter_placement == 'south':
        shelf_placement = KPtest.knapsack_placement(max_height, max_width, shelf_spec, shelf_height)
        shelf_placement = KPtest.add_FF(shelf_placement,shelf_spec, max_width)
        shelf_placement = flip.ccw(max_height, max_width, shelf_placement)
    num_shelf = len(shelf_placement)

    for i in range(num_shelf):
        shelf_placement[i]['x'] = shelf_placement[i]['x']+x
        shelf_placement[i]['y'] = shelf_placement[i]['y']+y
    num_shelf = len(shelf_placement)
    
    for i in range(num_shelf):
        if i ==0:
            shelf_name = 'FF'
            shelf_placement[i]['name'] = shelf_name
        else:
            shelf_name = f"{int(shelf_placement[i]['w'])}x{int(shelf_placement[i]['h'])}"
            shelf_placement[i]['name'] = shelf_name
    for i in range(num_shelf):
        print(f"{shelf_placement[i]['name']} : x={shelf_placement[i]['x']}, y={shelf_placement[i]['y']}, w={shelf_placement[i]['w']}, h={shelf_placement[i]['h']}")

    return shelf_placement