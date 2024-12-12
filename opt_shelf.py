from ortools.sat.python import cp_model
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib
from tools import get_feasible_area
from tools import coordinate_flipping as flip
from tools import get_feasible_area
from dxf_tools import dxf_manipulation
import re
import math

DualReductions = 0


def middle_object(obj_params, AISLE_SPACE, SPACE_WIDTH, SPACE_HEIGHT, unusable_gridcell1):
    unusable_gridcell = {}
    for key, values in unusable_gridcell1.items():
        tmp_cell = {}
        tmp_cell['x'] = int(values['x'])
        tmp_cell['y'] = int(values['y'])
        tmp_cell['w'] = int(values['w'])
        tmp_cell['h'] = int(values['h'])
        unusable_gridcell[key] = tmp_cell

    for item in unusable_gridcell.values():
        name = item.get('name')  # Use get to avoid KeyError
        if name == '前櫃檯':
            fixed_rect_x = item['x']
            fixed_rect_y = item['y']
            fixed_rect_width = item['w']
            fixed_rect_height = item['h']
            print(fixed_rect_x,fixed_rect_y,fixed_rect_width,fixed_rect_height)

    start_time = time.time()
    model = cp_model.CpModel()

    num_objects = len(obj_params)
    num_unusable_cells = len(unusable_gridcell)
    
    optgroup_2 = {}

    temp = 0
    for i in range(num_objects):
        if obj_params[i]['group']==2:
            optgroup_2.update({temp:obj_params[i]})
            temp+=1
    num_optgroup2 = len(optgroup_2)

    for i in range(num_optgroup2):
        if optgroup_2[i]['name']=='貨架區':
            shelf = i
            #print(shelf)
    

    s, t = {}, {}
    x, y, w, h = {}, {}, {}, {}
    # Binary variables
    for i in range(num_optgroup2):
        for k in range(num_unusable_cells):
            s[(i, k)] = model.NewBoolVar(f"s_{i}_{k}")
            t[(i, k)] = model.NewBoolVar(f"t_{i}_{k}")
    
    int_SPACE_WIDTH = math.floor(SPACE_WIDTH)
    int_SPACE_HEIGHT = math.floor(SPACE_HEIGHT)
    
    # Dimension variables
    x = [model.NewIntVar(0, int_SPACE_WIDTH, f'x_{i}') for i in range(num_optgroup2)]
    y = [model.NewIntVar(0, int_SPACE_HEIGHT, f'y_{i}') for i in range(num_optgroup2)]
    w = [model.NewIntVar(0, int_SPACE_WIDTH, f'w_{i}') for i in range(num_optgroup2)]
    h = [model.NewIntVar(0, int_SPACE_HEIGHT, f'h_{i}') for i in range(num_optgroup2)]

    # Set objective
    #model.setObjective(gp.quicksum(w[i]*h[i] for i in range(num_optgroup2)), GRB.MINIMIZE)
    #model.setParam('TimeLimit', 1800)
    product = model.NewIntVar(0, int_SPACE_WIDTH * int_SPACE_HEIGHT, f"product")
    model.AddMultiplicationEquality(product, [w[shelf], h[shelf]])

    
    model.Maximize(product)
    # Set constraints for general specifications

    # Boundary constraints
    for i in range(num_optgroup2):
        model.Add(x[i] + w[i] <= int_SPACE_WIDTH)
        model.Add(y[i] + h[i] <= int_SPACE_HEIGHT)
                
    # Length constraint
    model.Add(w[i]<=int_SPACE_WIDTH)
    model.Add(h[i]<=int_SPACE_HEIGHT)

    # Unusable grid cell constraint
    for i in range(num_optgroup2):
        for k in range(num_unusable_cells):
            int_x = math.floor(unusable_gridcell[k]['x'])
            int_right = math.ceil(unusable_gridcell[k]['x']+ unusable_gridcell[k]['w'])
            int_y = math.floor(unusable_gridcell[k]['y'])
            int_top = math.ceil(unusable_gridcell[k]['y'] + unusable_gridcell[k]['h'])
            model.Add(x[i] >= int_right + 1 - int_SPACE_WIDTH * (s[i,k] + t[i,k]))
            model.Add(int_x >= x[i] + w[i] - int_SPACE_WIDTH * (1 + s[i,k] - t[i,k]))
            model.Add(y[i] >= int_top + 1 - int_SPACE_HEIGHT * (1 - s[i,k] + t[i,k]))
            model.Add(int_y >= y[i] + h[i] - int_SPACE_HEIGHT * (2 - s[i,k] - t[i,k]))
    
    # Create the solver
    solver = cp_model.CpSolver()

    # Solve the model
    status = solver.Solve(model)
    end_time = time.time()
    result = {}
    shelf_area = {}

    # Print objective value and runtime
    if status == cp_model.OPTIMAL:
        print(f"Runtime: {end_time - start_time} seconds")
        print("Optimal solution found!")
        for i in range(num_optgroup2):
            result.update({i:{'x':solver.Value(x[i]), 'y':solver.Value(y[i]), 'w':solver.Value(w[i]), 'h':solver.Value(h[i]), 'name': optgroup_2[i]['name'],'type':'shelf area'}})
            print(f"{result[i]['name']} : x={result[i]['x']}, y={result[i]['y']}, w={result[i]['w']}, h={result[i]['h']}")
            if i == shelf:
                shelf_area.update({'x':solver.Value(x[i]), 'y':solver.Value(y[i]), 'w':solver.Value(w[i]), 'h':solver.Value(h[i]),'type':'shelf area'})
            
    else:
        print("No solution found.")
        
    return result, shelf_area, shelf



