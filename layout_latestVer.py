# add different aisle space specification, Tij and input
# add object orientation
# add 長邊靠牆
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from tools import get_dxf_points

DualReductions = 0
#Define the parameters and variables


obj_params = {
    0: {'w_h': [422,66], 'connect':[], 'fixed_wall': 'none'},
    1: {'w_h': [658,66], 'connect':[], 'fixed_wall': 'any'},
    2: {'w_h': [365,270], 'connect':[], 'fixed_wall': 'any'}, 
    3: {'w_h': [360,66], 'connect':[], 'fixed_wall': 'none'},
    4: {'w_h': [90,66], 'connect':[5], 'fixed_wall': 'any'},
    5: {'w_h': [90,66], 'connect':[6], 'fixed_wall': 'none'},
    6: {'w_h': [90,66], 'connect':[5], 'fixed_wall': 'none'},
    7: {'w_h': [310,225], 'connect':[], 'fixed_wall': 'any'},
    8: {'w_h': [95,59], 'connect':[], 'fixed_wall': 'any'},
    9: {'w_h': [185,90], 'connect':[], 'fixed_wall': 'any'},
    10: {'w_h': [396,76], 'connect':[], 'fixed_wall': 'none'},
    11: {'w_h': [396,76], 'connect':[], 'fixed_wall': 'none'},
    12: {'w_h': [396,76], 'connect':[], 'fixed_wall': 'none'},
    13: {'w_h': [396,76], 'connect':[], 'fixed_wall': 'none'},
    14: {'w_h': [396,76], 'connect':[], 'fixed_wall': 'none'},
    15: {'w_h': [396,76], 'connect':[], 'fixed_wall': 'none'},
    16: {'w_h': [396,76], 'connect':[], 'fixed_wall': 'none'},
    17: {'w_h': [396,76], 'connect':[], 'fixed_wall': 'none'}
}

unusable_gridcell = {
    0:{'x':0,'y':0,'w':100, 'h':30},
    1:{'x':500,'y':0,'w':150, 'h':50}
}
num_objects = len(obj_params)
num_unusable_cells = len(unusable_gridcell)


# Space parameters
SPACE_WIDTH = 1700
SPACE_HEIGHT = 1100
AISLE_SPACE = 100

# Fixed object position
fixed_room = 0
x_fixed = 0
y_fixed = 0



def layout_opt(obj_params, num_objects, AISLE_SPACE, SPACE_WIDTH, SPACE_HEIGHT, unusable_gridcell, num_unusable_cells):
    # Create a Gurobi model
    start_time = time.time()
    model = gp.Model("layout_generation_front desk")
    model.params.NonConvex = 2


    # Binary variables
    p = {}
    for i in range(num_objects):
        for j in range(num_objects):
            if i != j:
                p[i, j] = model.addVar(vtype=GRB.BINARY, name=f"p_{i}_{j}")
    q = {}
    for i in range(num_objects):
        for j in range(num_objects):
            if i != j:
                q[i, j] = model.addVar(vtype=GRB.BINARY, name=f"q_{i}_{j}")

    s = {}
    for i in range(num_objects):
        for k in range(num_unusable_cells):
            s[i, k] = model.addVar(vtype=GRB.BINARY, name=f"s_{i}_{k}")
    t = {}
    for i in range(num_objects):
        for k in range(num_unusable_cells):
            t[i, k] = model.addVar(vtype=GRB.BINARY, name=f"t_{i}_{k}")

    orientation = {}
    for i in range(num_objects):
        orientation[i] = model.addVar(vtype=GRB.BINARY, name=f"orientation_{i}")
    # Dimension variables
    x = {}
    for k in range(num_objects):
        x[k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"x_{k}")
    
    y = {}
    for k in range(num_objects):
        y[k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"y_{k}")
    w = {}
    for k in range(num_objects):
        w[k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"w_{k}")
    h = {}
    for k in range(num_objects):
        h[k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"h_{k}")

    select = {}
    for i in range(num_objects):
        for k in range(4):
            select[i,k] = model.addVar(vtype=GRB.BINARY, name=f"select_{i,k}")

    select2 = {}
    for i in range(num_objects):
        for k in range(4):
            select2[i,k] = model.addVar(vtype=GRB.BINARY, name=f"select2_{i,k}")
    
    T = {}
    for i in range(num_objects):
        for k in range(num_objects):
            T[i,k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"T_{i,k}")


    # Set objective
    #model.setObjective(gp.quicksum(w[i]*h[i] for i in range(n)), GRB.MINIMIZE)
    #model.setParam('TimeLimit', 1800)
    total_area = gp.quicksum(w[i] * h[i] for i in range(num_objects))
    coor =gp.quicksum(x[i] + y[i] for i in range(num_objects))
    model.setObjective((total_area), GRB.MINIMIZE)
    # Set constraints for general specifications
    # Connectivity constraint
    for i in range(num_objects):
        if not obj_params[i]['connect']:
            print(f'No connectivity constraint for object {i}')
        else:
            for j in obj_params[i]['connect']:
                print(f'connect{j}')
                model.addConstr(x[i] + w[i] >= x[j] - SPACE_WIDTH*(p[i,j] + q[i,j]), name="Connectivity Constraint 1")
                model.addConstr(y[i] + h[i] >= y[j] - SPACE_HEIGHT*(1 + p[i,j] - q[i,j]), name="Connectivity Constraint 2")
                model.addConstr(x[j] + w[j] >= x[i] - SPACE_WIDTH*(1 - p[i,j] + q[i,j]), name = "Connectivity Constraint 3")
                model.addConstr(y[j] + h[j] >= y[i] - SPACE_HEIGHT*(2 - p[i,j] - q[i,j]), name = "Connectivity Constraint 4")
                model.addConstr(0.5*(w[i]+w[j]) >= T[i,j] + (y[j] - y[i]) - SPACE_WIDTH*(p[i,j] + q[i,j]), name="overlap constraint_18")
                model.addConstr(0.5*(h[i]+h[j]) >= T[i,j] + (x[j] - x[i]) - SPACE_HEIGHT*(2 - p[i,j] - q[i,j]), name="overlap constraint_19")
                model.addConstr(0.5*(w[i]+w[j]) >= T[i,j] + (y[i] - y[j]) - SPACE_WIDTH*(1 - p[i,j] + q[i,j]), name="overlap constraint_20")
                model.addConstr(0.5*(h[i]+h[j]) >= T[i,j] + (x[i] - x[j]) - SPACE_HEIGHT*(1 + p[i,j] - q[i,j]), name="overlap constraint_21")

    # Boundary constraints
    for i in range(num_objects):
        model.addConstr(x[i] + w[i] <= SPACE_WIDTH, name="Boundary constraint for x")
        model.addConstr(y[i] + h[i] <= SPACE_HEIGHT, name="Boundary constraint for y")
    
    # Fixed border constraint
    for i in range(num_objects):
        if obj_params[i]['fixed_wall'] == 'north':
            model.addConstr(y[i] == 0, name="North border constraint")
        elif obj_params[i]['fixed_wall']== 'south':
            model.addConstr(y[i]+max(obj_params[i]['w_h']) == SPACE_HEIGHT, name="South border constraint")
        elif obj_params[i]['fixed_wall']== 'east':
            model.addConstr(x[i]+w[i] == SPACE_WIDTH, name="East border constraint")
        elif obj_params[i]['fixed_wall']== 'west':
            model.addConstr(x[i] == 0, name="West border constraint")
        
        elif obj_params[i]['fixed_wall']== 'any':
            # 選靠哪面牆
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(obj_params[i]['w_h'])-SPACE_WIDTH+1)*select[i,1]+(y[i]+1)*select[i,2]+(y[i]+min(obj_params[i]['w_h'])-SPACE_HEIGHT+1)*select[i,3]==1, name='any constraint')
        
        else:
            print(f'No fixed wall constraint for object {i}')

    
    # Non-intersecting with aisle constraint
    for i in range(num_objects):
        for j in range(num_objects):
            if not obj_params[i]['connect'] and i != j:
                if [i, j] == [1,0] or [i,j]==[0,1]:
                    model.addConstr((orientation[i]==0)>>(x[i] + w[i] + 110 <= x[j] + SPACE_WIDTH * (p[i,j] + q[i,j])), name="Non-intersecting Constraint 1")
                    model.addConstr((orientation[i]==1)>>(y[i] + h[i] + 110 <= y[j] + SPACE_HEIGHT * (1 + p[i,j] - q[i,j])), name="Non-intersecting Constraint 2")
                    model.addConstr((orientation[i]==0)>>(x[j] + w[j] + 110 <= x[i] + SPACE_WIDTH * (1 - p[i,j] + q[i,j])), name = "Non-intersecting Constraint 3")
                    model.addConstr((orientation[i]==1)>>(y[j] + h[j] + 110 <= y[i] + SPACE_HEIGHT * (2 - p[i,j] - q[i,j])), name = "Non-intersecting Constraint 4")

                    model.addConstr((orientation[i]==0)>>(x[i] + w[i] + 110 >= x[j] - SPACE_WIDTH * (p[i,j] + q[i,j])), name="Non-intersecting Constraint 1")
                    model.addConstr((orientation[i]==1)>>(y[i] + h[i] + 110 >= y[j] - SPACE_HEIGHT * (1 + p[i,j] - q[i,j])), name="Non-intersecting Constraint 2")
                    model.addConstr((orientation[i]==0)>>(x[j] + w[j] + 110 >= x[i] - SPACE_WIDTH * (1 - p[i,j] + q[i,j])), name = "Non-intersecting Constraint 3")
                    model.addConstr((orientation[i]==1)>>(y[j] + h[j] + 110 >= y[i] - SPACE_HEIGHT * (2 - p[i,j] - q[i,j])), name = "Non-intersecting Constraint 4")
                else:
                    # non-intersecting constraints
                    # object i to the left of object j
                    model.addConstr(x[i] + w[i] + AISLE_SPACE <= x[j] + SPACE_WIDTH * (p[i,j] + q[i,j]), name="Non-intersecting Constraint 1")
                    
                    # object i above object j
                    model.addConstr(y[i] + h[i] + AISLE_SPACE <= y[j] + SPACE_HEIGHT * (1 + p[i,j] - q[i,j]), name="Non-intersecting Constraint 2")
                    
                    # object i to the right of object j
                    model.addConstr(x[j] + w[j] + AISLE_SPACE <= x[i] + SPACE_WIDTH * (1 - p[i,j] + q[i,j]), name = "Non-intersecting Constraint 3")
                    
                    # object i below object j
                    model.addConstr(y[j] + h[j] + AISLE_SPACE <= y[i] + SPACE_HEIGHT * (2 - p[i,j] - q[i,j]), name = "Non-intersecting Constraint 4")
            elif i!=j:
                model.addConstr(x[i] + w[i] <= x[j] + SPACE_WIDTH * (p[i,j] + q[i,j]), name="Non-intersecting Constraint 1")
                model.addConstr(y[i] + h[i] <= y[j] + SPACE_HEIGHT * (1 + p[i,j] - q[i,j]), name="Non-intersecting Constraint 2")
                model.addConstr(x[j] + w[j] <= x[i] + SPACE_WIDTH * (1 - p[i,j] + q[i,j]), name = "Non-intersecting Constraint 3")
                model.addConstr(y[j] + h[j] <= y[i] + SPACE_HEIGHT * (2 - p[i,j] - q[i,j]), name = "Non-intersecting Constraint 4")

    # Length constraint
    for i in range(num_objects):
        model.addConstr(w[i]==[min(obj_params[i]['w_h']),max(obj_params[i]['w_h'])] , name="Length Constraint 1")
        model.addConstr(h[i] == [min(obj_params[i]['w_h']), max(obj_params[i]['w_h'])], name="Height Constraint 2")
    
    # Unusable grid cell constraint
    for i in range(num_objects):
        for k in range(num_unusable_cells):
            model.addConstr(x[i] >= unusable_gridcell[k]['x']+ unusable_gridcell[k]['w'] + 1 - SPACE_WIDTH * (s[i,k] + t[i,k]), name="Unusable grid cell 1")
            model.addConstr(unusable_gridcell[k]['x'] >= x[i] + w[i] - SPACE_WIDTH * (1 + s[i,k] - t[i,k]), name="Unusable grid cell 2")
            model.addConstr(y[i] >= unusable_gridcell[k]['y'] + unusable_gridcell[k]['h'] + 1 - SPACE_HEIGHT * (1 - s[i,k] + t[i,k]), name = "Unusable grid cell 3")
            model.addConstr(unusable_gridcell[k]['y'] >= y[i] + h[i] - SPACE_HEIGHT * (2 - s[i,k] - t[i,k]), name = "Unusable grid cell 4")
    # Orientation constraint
    for i in range(num_objects):
        model.addConstr(w[i] == h[i]*((max(obj_params[i]['w_h'])/min(obj_params[i]['w_h']))*orientation[i]+(min(obj_params[i]['w_h'])/max(obj_params[i]['w_h']))*(1-orientation[i])))
    
    # Set constraints related to front desk
    # Shelf vertical to front desk
    for i in range(10,18):
        model.addConstr(orientation[0]+orientation[i]==1)
    # Same orientation for front desks
    model.addConstr(orientation[0]==orientation[1])
    model.addConstr((orientation[0]==1)>>(x[0]==x[1]))
    model.addConstr((orientation[0]==0)>>(y[0]==y[1]))

    # Constraint for object long side againt wall
    for i in range(num_objects):
        for j in range(num_objects):
            if [i, j] == [1,0]:
                model.addConstr((q[i,j]==1)>>(orientation[i]==1))
                model.addConstr((q[i,j]==0)>>(orientation[i]==0))

    # Optimize the model
    model.optimize()
    end_time = time.time()
    result = {}


    # Print objective value and runtime
    if model.status == GRB.OPTIMAL:
        print(f"Runtime: {end_time - start_time} seconds")
        print("Optimal solution found!")
        for i in range(num_objects):
            print(f"Object {i}: x={x[i].X}, y={y[i].X}, w={w[i].X}, h={h[i].X}")
            result.update({i:{'x':x[i].X, 'y':y[i].X, 'w':w[i].X, 'h':h[i].X}})
        print("Total area:", model.objVal)
        
    elif model.status == GRB.INFEASIBLE:
        print("The problem is infeasible. Review your constraints.")
    else:
        print("No solution found.")
        
        model.computeIIS()
        for c in model.getConstrs():
            if c.IISConstr: print(f'\t{c.constrname}: {model.getRow(c)} {c.Sense} {c.RHS}')
        pass
    
    return result
def layout_plot(result, unusable_gridcell):
    
    # Define room data
    data = result

    # Define total space dimensions
    total_space = {'width': SPACE_WIDTH, 'height': SPACE_HEIGHT}

    # Create a new figure
    plt.figure(figsize=(8, 8))

    # Plot total space
    plt.gca().add_patch(plt.Rectangle((0, 0), total_space['width'], total_space['height'], fill=None, edgecolor='blue', label='Total Space'))

    # Plot each object
    for object_id, object_info in data.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']
        plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=f'object {object_id}'))
        plt.text(x + w/2, y + h/2, f'object {object_id}', ha='center', va='center', color='red', fontsize=8)
    
    # Plot obstacle
    # Parameters adaptation
    obstacle_positions = [(unusable_gridcell[k]['x'], unusable_gridcell[k]['y']) for k in unusable_gridcell]
    obstacle_dimensions = [(unusable_gridcell[k]['w'], unusable_gridcell[k]['h']) for k in unusable_gridcell]
    for k, (x_u, y_u) in enumerate(obstacle_positions):
        w_u, h_u = obstacle_dimensions[k]
        plt.gca().add_patch(plt.Rectangle((x_u, y_u), w_u, h_u, fill=None, edgecolor='red', label = 'x'))
        plt.text(x_u + w_u/2, y_u + h_u/2, 'x', ha='center', va='center', color='red', fontsize=8)
    # Set plot limits and labels
    plt.xlim(0, total_space['width'])
    plt.ylim(total_space['height'], 0)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Space Layout')

    # Show plot
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

def draw_dxf(result,name,W,H):
    points = {}
    doc = ezdxf.new("R2000")
    msp = doc.modelspace()
    for object_id, object_info in result.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']
        point = [(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)]
        points.update({object_id:point})
        
    
    for object_id, point in points.items():
        msp.add_text(object_id, dxfattribs={"layer": "OBJECTLAYER"}).set_placement((point[0]), align=TextEntityAlignment.CENTER)
        msp.add_lwpolyline(point)
    msp.add_lwpolyline([(0,0),(W,0),(W,H),(0,H),(0,0)])
    doc.saveas(f"{name}.dxf")



if __name__ == '__main__':
    result = layout_opt(obj_params, num_objects, AISLE_SPACE,SPACE_WIDTH, SPACE_HEIGHT, unusable_gridcell, num_unusable_cells)
    draw_dxf(result,"20240620_result",SPACE_WIDTH,SPACE_HEIGHT)
    layout_plot(result, unusable_gridcell)
    
