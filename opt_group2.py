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

DualReductions = 0


def middle_object(obj_params, AISLE_SPACE, SPACE_WIDTH, SPACE_HEIGHT, unusable_gridcell):
    for key, value in unusable_gridcell.items():
        value['x'] = int(value['x'])
        value['y'] = int(value['y'])
        value['w'] = int(value['w'])
        value['h'] = int(value['h'])
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
    
    # Dimension variables
    x = [model.NewIntVar(0, SPACE_WIDTH, f'x_{i}') for i in range(num_optgroup2)]
    y = [model.NewIntVar(0, SPACE_HEIGHT, f'y_{i}') for i in range(num_optgroup2)]
    w = [model.NewIntVar(0, SPACE_WIDTH, f'w_{i}') for i in range(num_optgroup2)]
    h = [model.NewIntVar(0, SPACE_HEIGHT, f'h_{i}') for i in range(num_optgroup2)]

    # Set objective
    #model.setObjective(gp.quicksum(w[i]*h[i] for i in range(num_optgroup2)), GRB.MINIMIZE)
    #model.setParam('TimeLimit', 1800)
    product = model.NewIntVar(0, SPACE_WIDTH * SPACE_HEIGHT, f"product")
    model.AddMultiplicationEquality(product, [w[shelf], h[shelf]])

    
    model.Maximize(product)
    # Set constraints for general specifications

    # Boundary constraints
    for i in range(num_optgroup2):
        model.Add(x[i] + w[i] <= SPACE_WIDTH)
        model.Add(y[i] + h[i] <= SPACE_HEIGHT)
                
    # Length constraint
    model.Add(w[i]<=SPACE_WIDTH)
    model.Add(h[i]<=SPACE_HEIGHT)

    # Unusable grid cell constraint
    for i in range(num_optgroup2):
        for k in range(num_unusable_cells):
            model.Add(x[i] >= unusable_gridcell[k]['x']+ unusable_gridcell[k]['w'] + 1 - SPACE_WIDTH * (s[i,k] + t[i,k]))
            model.Add(unusable_gridcell[k]['x'] >= x[i] + w[i] - SPACE_WIDTH * (1 + s[i,k] - t[i,k]))
            model.Add(y[i] >= unusable_gridcell[k]['y'] + unusable_gridcell[k]['h'] + 1 - SPACE_HEIGHT * (1 - s[i,k] + t[i,k]))
            model.Add(unusable_gridcell[k]['y'] >= y[i] + h[i] - SPACE_HEIGHT * (2 - s[i,k] - t[i,k]))
    
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
            result.update({i:{'x':solver.Value(x[i]), 'y':solver.Value(y[i]), 'w':solver.Value(w[i]), 'h':solver.Value(h[i]), 'name': optgroup_2[i]['name']}})
            print(f"{result[i]['name']} : x={result[i]['x']}, y={result[i]['y']}, w={result[i]['w']}, h={result[i]['h']}")
            if i == shelf:
                shelf_area.update({'x':solver.Value(x[i]), 'y':solver.Value(y[i]), 'w':solver.Value(w[i]), 'h':solver.Value(h[i])})
            
    else:
        print("No solution found.")

    return result, shelf_area, shelf



