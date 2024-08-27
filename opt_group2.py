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

DualReductions = 0


def middle_object(obj_params, AISLE_SPACE, SPACE_WIDTH, SPACE_HEIGHT, unusable_gridcell):
        # Create a Gurobi model
    start_time = time.time()
    model = gp.Model("layout_generation_front desk")
    model.params.NonConvex = 2

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
    

    p, q, s, t, orientation = {}, {}, {}, {}, {}
    x, y, w, h, select, T = {}, {}, {}, {}, {}, {}
    # Binary variables
    for i in range(num_optgroup2):
        for j in range(num_optgroup2):
            if i != j:
                p[i, j] = model.addVar(vtype=GRB.BINARY, name=f"p_{i}_{j}")
                q[i, j] = model.addVar(vtype=GRB.BINARY, name=f"q_{i}_{j}")
        for k in range(num_unusable_cells):
            s[i, k] = model.addVar(vtype=GRB.BINARY, name=f"s_{i}_{k}")
            t[i, k] = model.addVar(vtype=GRB.BINARY, name=f"t_{i}_{k}")
        orientation[i] = model.addVar(vtype=GRB.BINARY, name=f"orientation_{i}")

    # Dimension variables
    for i in range(num_optgroup2):
        x[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"x_{i}")
        y[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"y_{i}")
        w[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"w_{i}")
        h[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"h_{i}")

        for k in range(4):
            select[i,k] = model.addVar(vtype=GRB.BINARY, name=f"select_{i,k}")
    
        for j in range(num_optgroup2):
            T[i,j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"T_{i,j}")


    # Set objective
    #model.setObjective(gp.quicksum(w[i]*h[i] for i in range(num_optgroup2)), GRB.MINIMIZE)
    #model.setParam('TimeLimit', 1800)
    model.setObjective(w[shelf]*h[shelf], GRB.MAXIMIZE)
    # Set constraints for general specifications

    # Boundary constraints
    for i in range(num_optgroup2):
        model.addConstr(x[i] + w[i] <= SPACE_WIDTH, name="Boundary constraint for x")
        model.addConstr(y[i] + h[i] <= SPACE_HEIGHT, name="Boundary constraint for y")
    
    # Fixed border constraint
    for i in range(num_optgroup2):
        if not optgroup_2[i]['fixed_wall']:
            print(f'No fixed wall constraint for object {i}')
        elif optgroup_2[i]['fixed_wall']== 'any':
            # 選靠哪面牆
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((select[i,0]==1)>>(x[i]==0))
            model.addConstr((select[i,1]==1)>>(x[i]+min(optgroup_2[i]['w_h']) == SPACE_WIDTH))
            model.addConstr((select[i,2]==1)>>(y[i]==0))
            model.addConstr((select[i,3]==1)>>(y[i]+min(optgroup_2[i]['w_h']) == SPACE_HEIGHT))
        elif optgroup_2[i]['fixed_wall'] == 'north':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((select[i,0]==1)>>(x[i]==0))
            model.addConstr((select[i,1]==1)>>(x[i]+min(optgroup_2[i]['w_h']) == SPACE_WIDTH))
            model.addConstr((select[i,2]==1)>>(y[i]==0))
            model.addConstr((select[i,3]==1)>>(y[i]+min(optgroup_2[i]['w_h']) == SPACE_HEIGHT))
            model.addConstr(select[i,2]==1, name="North border constraint")
        elif optgroup_2[i]['fixed_wall']== 'south':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((select[i,0]==1)>>(x[i]==0))
            model.addConstr((select[i,1]==1)>>(x[i]+min(optgroup_2[i]['w_h']) == SPACE_WIDTH))
            model.addConstr((select[i,2]==1)>>(y[i]==0))
            model.addConstr((select[i,3]==1)>>(y[i]+min(optgroup_2[i]['w_h']) == SPACE_HEIGHT))
            model.addConstr(select[i,3]==1, name="South border constraint")
        elif optgroup_2[i]['fixed_wall']== 'east':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((select[i,0]==1)>>(x[i]==0))
            model.addConstr((select[i,1]==1)>>(x[i]+min(optgroup_2[i]['w_h']) == SPACE_WIDTH))
            model.addConstr((select[i,2]==1)>>(y[i]==0))
            model.addConstr((select[i,3]==1)>>(y[i]+min(optgroup_2[i]['w_h']) == SPACE_HEIGHT))
            model.addConstr(select[i,1]==1, name="East border constraint")
        elif optgroup_2[i]['fixed_wall']== 'west':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((select[i,0]==1)>>(x[i]==0))
            model.addConstr((select[i,1]==1)>>(x[i]+min(optgroup_2[i]['w_h']) == SPACE_WIDTH))
            model.addConstr((select[i,2]==1)>>(y[i]==0))
            model.addConstr((select[i,3]==1)>>(y[i]+min(optgroup_2[i]['w_h']) == SPACE_HEIGHT))
            model.addConstr(select[i,0]==1, name="West border constraint")

    
    # Non-intersecting with aisle constraint
    for i in range(num_optgroup2):
        for j in range(num_optgroup2):
            if i != j:
                model.addConstr(x[i] + w[i] + AISLE_SPACE <= x[j] + SPACE_WIDTH * (p[i,j] + q[i,j]), name="Non-intersecting Constraint 1")
                model.addConstr(y[i] + h[i] + AISLE_SPACE <= y[j] + SPACE_HEIGHT * (1 + p[i,j] - q[i,j]), name="Non-intersecting Constraint 2")
                model.addConstr(x[j] + w[j] + AISLE_SPACE <= x[i] + SPACE_WIDTH * (1 - p[i,j] + q[i,j]), name = "Non-intersecting Constraint 3")
                model.addConstr(y[j] + h[j] + AISLE_SPACE <= y[i] + SPACE_HEIGHT * (2 - p[i,j] - q[i,j]), name = "Non-intersecting Constraint 4")

    # Length constraint
    for i in range(num_optgroup2):
        if i != shelf:
            model.addConstr(w[i]==[min(optgroup_2[i]['w_h']),max(optgroup_2[i]['w_h'])] , name="Length Constraint 1")
            model.addConstr(h[i] == [min(optgroup_2[i]['w_h']), max(optgroup_2[i]['w_h'])], name="Height Constraint 2")
   
    model.addConstr(w[shelf]<=SPACE_WIDTH, name="Shelf area 1")
    model.addConstr(h[shelf]<=SPACE_HEIGHT, name="Shelf area2")

    # Unusable grid cell constraint
    for i in range(num_optgroup2):
        for k in range(num_unusable_cells):
            model.addConstr(x[i] >= unusable_gridcell[k]['x']+ unusable_gridcell[k]['w'] + 1 - SPACE_WIDTH * (s[i,k] + t[i,k]), name="Unusable grid cell 1")
            model.addConstr(unusable_gridcell[k]['x'] >= x[i] + w[i] - SPACE_WIDTH * (1 + s[i,k] - t[i,k]), name="Unusable grid cell 2")
            model.addConstr(y[i] >= unusable_gridcell[k]['y'] + unusable_gridcell[k]['h'] + 1 - SPACE_HEIGHT * (1 - s[i,k] + t[i,k]), name = "Unusable grid cell 3")
            model.addConstr(unusable_gridcell[k]['y'] >= y[i] + h[i] - SPACE_HEIGHT * (2 - s[i,k] - t[i,k]), name = "Unusable grid cell 4")
    # Orientation constraint
    for i in range(num_optgroup2):
        if i!= shelf:
            model.addConstr(w[i] == h[i]*((max(optgroup_2[i]['w_h'])/min(optgroup_2[i]['w_h']))*orientation[i]
                                          +(min(optgroup_2[i]['w_h'])/max(optgroup_2[i]['w_h']))*(1-orientation[i])))
    
    

    # Optimize the model
    model.optimize()
    end_time = time.time()
    result = {}
    shelf_area = {}

    # Print objective value and runtime
    if model.status == GRB.OPTIMAL:
        print(f"Runtime: {end_time - start_time} seconds")
        print("Optimal solution found!")
        for i in range(num_optgroup2):
            result.update({i:{'x':x[i].X, 'y':y[i].X, 'w':w[i].X, 'h':h[i].X, 'name': optgroup_2[i]['name']}})
            print(f"{result[i]['name']} : x={result[i]['x']}, y={result[i]['y']}, w={result[i]['w']}, h={result[i]['h']}")
            if i == shelf:
                shelf_area.update({'x':x[i].X, 'y':y[i].X, 'w':w[i].X, 'h':h[i].X})
            
    elif model.status == GRB.INFEASIBLE:
        print("The problem is infeasible. Review your constraints.")
    else:
        print("No solution found.")
        
        model.computeIIS()
        for c in model.getConstrs():
            if c.IISConstr: print(f'\t{c.constrname}: {model.getRow(c)} {c.Sense} {c.RHS}')
        pass
    return result, shelf_area, shelf



