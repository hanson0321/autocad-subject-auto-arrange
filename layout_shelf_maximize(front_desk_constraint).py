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
import matplotlib


DualReductions = 0
#Define the parameters and variables

# Space parameters
W = 2500
H = 1800
A = 100
'''
obj_params = {
    0: {'w_h': [W,H], 'connect':[], 'fixed_wall': 'none'},
    1: {'w_h': [422,66], 'connect':[], 'fixed_wall': 'none'},
    2: {'w_h': [658,66], 'connect':[], 'fixed_wall': 'any'},
    3: {'w_h': [365,270], 'connect':[], 'fixed_wall': 'any'}, 
    4: {'w_h': [360,66], 'connect':[], 'fixed_wall': 'none'},
    5: {'w_h': [90,66], 'connect':[], 'fixed_wall': 'none'},
    6: {'w_h': [90,66], 'connect':[], 'fixed_wall': 'none'},
    7: {'w_h': [90,66], 'connect':[], 'fixed_wall': 'none'},
    8: {'w_h': [310,225], 'connect':[], 'fixed_wall': 'any'},
    9: {'w_h': [95,59], 'connect':[], 'fixed_wall': 'any'},
    10: {'w_h': [185,90], 'connect':[], 'fixed_wall': 'any'},
    11: {'w_h': [100,85], 'connect':[], 'fixed_wall': 'none'},
    12: {'w_h': [83,64], 'connect':[], 'fixed_wall': 'none'},
    13: {'w_h': [80,55], 'connect':[], 'fixed_wall': 'none'}
}
}
'''
obj_params = {
    0: {'w_h': [W,H], 'connect':[], 'fixed_wall': 'none'},
    1: {'w_h': [422,66], 'connect':[], 'fixed_wall': 'none'},
    2: {'w_h': [658,66], 'connect':[], 'fixed_wall': 'any'},
    3: {'w_h': [365,270], 'connect':[], 'fixed_wall': 'any'}, 
    4: {'w_h': [360,66], 'connect':[], 'fixed_wall': 'none'},
    5: {'w_h': [90,66], 'connect':[], 'fixed_wall': 'any'},
    6: {'w_h': [90,66], 'connect':[], 'fixed_wall': 'any'},
    7: {'w_h': [90,66], 'connect':[], 'fixed_wall': 'any'},
    8: {'w_h': [310,225], 'connect':[], 'fixed_wall': 'any'},
    9: {'w_h': [95,59], 'connect':[], 'fixed_wall': 'any'},
    10: {'w_h': [185,90], 'connect':[], 'fixed_wall': 'any'},
    11: {'w_h': [100,85], 'connect':[], 'fixed_wall': 'none'},
    12: {'w_h': [83,64], 'connect':[], 'fixed_wall': 'none'}
}

'''
0: "貨架區",
1: "前櫃檯",
2: "後櫃檯",
3: "WI",
4: "6個FF (360x66)",
5: "雙溫櫃",
6: "單溫櫃",
7: "OC",
8: "RI",
9: "EC",
10: "子母櫃",
11: "ATM",
12: "影印",
13: "KIOSK",
14: "單人座位",
15: "雙人座位",
16: "分享桌座位"
'''
unusable_gridcell = {

}
n = len(obj_params)
m = len(unusable_gridcell)


# Fixed object position
fixed_room = 0
x_fixed = 0
y_fixed = 0



def layout_opt(obj_params, n, A, W, H, unusable_gridcell, m):
    # Create a Gurobi model
    start_time = time.time()
    model = gp.Model("layout_generation_front desk")
    model.params.NonConvex = 2
    #model.params.NoRelHeurTime = 600


    # Binary variables
    p = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                p[i, j] = model.addVar(vtype=GRB.BINARY, name=f"p_{i}_{j}")
    q = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                q[i, j] = model.addVar(vtype=GRB.BINARY, name=f"q_{i}_{j}")

    s = {}
    for i in range(n):
        for k in range(m):
            s[i, k] = model.addVar(vtype=GRB.BINARY, name=f"s_{i}_{k}")
    t = {}
    for i in range(n):
        for k in range(m):
            t[i, k] = model.addVar(vtype=GRB.BINARY, name=f"t_{i}_{k}")

    orientation = {}
    for i in range(n):
        orientation[i] = model.addVar(vtype=GRB.BINARY, name=f"orientation_{i}")
    # Dimension variables
    x = {}
    for k in range(n):
        x[k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"x_{k}")
    
    y = {}
    for k in range(n):
        y[k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"y_{k}")
    w = {}
    for k in range(n):
        w[k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"w_{k}")
    h = {}
    for k in range(n):
        h[k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"h_{k}")

    select = {}
    for i in range(n):
        for k in range(4):
            select[i,k] = model.addVar(vtype=GRB.BINARY, name=f"select_{i,k}")

    select2 = {}
    for i in range(n):
        for k in range(4):
            select2[i,k] = model.addVar(vtype=GRB.BINARY, name=f"select2_{i,k}")
    
    T = {}
    for i in range(n):
        for k in range(n):
            T[i,k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"T_{i,k}")


    # Set objective
    #model.setObjective(gp.quicksum(w[i]*h[i] for i in range(n)), GRB.MINIMIZE)
    #model.setParam('TimeLimit', 1800)
    total_area = gp.quicksum(w[i] * h[i] for i in range(n))
    coor =gp.quicksum(x[i] + y[i] for i in range(n))
    model.setObjective(w[0]*h[0], GRB.MAXIMIZE)
    # Set constraints for general specifications
    # Connectivity constraint
    for i in range(n):
        if not obj_params[i]['connect']:
            pass
        else:
            for j in obj_params[i]['connect']:
                print(f'Object {i} and Object {j} should be connected')
                model.addConstr(x[i] + w[i] >= x[j] - W*(p[i,j] + q[i,j]), name="Connectivity Constraint 1")
                model.addConstr(y[i] + h[i] >= y[j] - H*(1 + p[i,j] - q[i,j]), name="Connectivity Constraint 2")
                model.addConstr(x[j] + w[j] >= x[i] - W*(1 - p[i,j] + q[i,j]), name = "Connectivity Constraint 3")
                model.addConstr(y[j] + h[j] >= y[i] - H*(2 - p[i,j] - q[i,j]), name = "Connectivity Constraint 4")
                model.addConstr(0.5*(w[i]+w[j]) >= T[i,j] + (y[j] - y[i]) - W*(p[i,j] + q[i,j]), name="overlap constraint_18")
                model.addConstr(0.5*(h[i]+h[j]) >= T[i,j] + (x[j] - x[i]) - H*(2 - p[i,j] - q[i,j]), name="overlap constraint_19")
                model.addConstr(0.5*(w[i]+w[j]) >= T[i,j] + (y[i] - y[j]) - W*(1 - p[i,j] + q[i,j]), name="overlap constraint_20")
                model.addConstr(0.5*(h[i]+h[j]) >= T[i,j] + (x[i] - x[j]) - H*(1 + p[i,j] - q[i,j]), name="overlap constraint_21")

    # Boundary constraints
    for i in range(n):
        model.addConstr(x[i] + w[i] <= W, name="Boundary constraint for x")
        model.addConstr(y[i] + h[i] <= H, name="Boundary constraint for y")
    
    # Fixed border constraint
    for i in range(n):
        if obj_params[i]['fixed_wall'] == 'north':
            model.addConstr(y[i] == 0, name="North border constraint")
        elif obj_params[i]['fixed_wall']== 'south':
            model.addConstr(y[i]+max(obj_params[i]['w_h']) == H, name="South border constraint")
        elif obj_params[i]['fixed_wall']== 'east':
            model.addConstr(x[i]+w[i] == W, name="East border constraint")
        elif obj_params[i]['fixed_wall']== 'west':
            model.addConstr(x[i] == 0, name="West border constraint")
        
        elif obj_params[i]['fixed_wall']== 'any':
            # 選靠哪面牆
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(obj_params[i]['w_h'])-W+1)*select[i,1]+(y[i]+1)*select[i,2]+(y[i]+min(obj_params[i]['w_h'])-H+1)*select[i,3]==1, name='any constraint')
        
        else:
            pass

    
    # Non-intersecting with aisle constraint
    for i in range(n):
        for j in range(n):
            if not obj_params[i]['connect'] and i != j:
                if [i, j] == [2,1] or [i,j]==[1,2]:
                    model.addConstr((orientation[i]==0)>>(x[i] + w[i] + 110 <= x[j] + W * (p[i,j] + q[i,j])), name="Non-intersecting Constraint 1")
                    model.addConstr((orientation[i]==1)>>(y[i] + h[i] + 110 <= y[j] + H * (1 + p[i,j] - q[i,j])), name="Non-intersecting Constraint 2")
                    model.addConstr((orientation[i]==0)>>(x[j] + w[j] + 110 <= x[i] + W * (1 - p[i,j] + q[i,j])), name = "Non-intersecting Constraint 3")
                    model.addConstr((orientation[i]==1)>>(y[j] + h[j] + 110 <= y[i] + H * (2 - p[i,j] - q[i,j])), name = "Non-intersecting Constraint 4")
                else:
                    model.addConstr(x[i] + w[i] + A <= x[j] + W * (p[i,j] + q[i,j]), name="Non-intersecting Constraint 1")
                    model.addConstr(y[i] + h[i] + A <= y[j] + H * (1 + p[i,j] - q[i,j]), name="Non-intersecting Constraint 2")
                    model.addConstr(x[j] + w[j] + A <= x[i] + W * (1 - p[i,j] + q[i,j]), name = "Non-intersecting Constraint 3")
                    model.addConstr(y[j] + h[j] + A <= y[i] + H * (2 - p[i,j] - q[i,j]), name = "Non-intersecting Constraint 4")
            elif i!=j:
                model.addConstr(x[i] + w[i] <= x[j] + W * (p[i,j] + q[i,j]), name="Non-intersecting Constraint 1")
                model.addConstr(y[i] + h[i] <= y[j] + H * (1 + p[i,j] - q[i,j]), name="Non-intersecting Constraint 2")
                model.addConstr(x[j] + w[j] <= x[i] + W * (1 - p[i,j] + q[i,j]), name = "Non-intersecting Constraint 3")
                model.addConstr(y[j] + h[j] <= y[i] + H * (2 - p[i,j] - q[i,j]), name = "Non-intersecting Constraint 4")

    # Length constraint
    for i in range(n):
        if i != 0:
            model.addConstr(w[i]==[min(obj_params[i]['w_h']),max(obj_params[i]['w_h'])] , name="Length Constraint 1")
            model.addConstr(h[i] == [min(obj_params[i]['w_h']), max(obj_params[i]['w_h'])], name="Height Constraint 2")
   
    model.addConstr(w[0]<=W, name="Shelf area 1")
    model.addConstr(h[0]<=H, name="Shelf area2")

    # Unusable grid cell constraint
    for i in range(n):
        for k in range(m):
            model.addConstr(x[i] >= unusable_gridcell[k]['x']+ unusable_gridcell[k]['w'] + 1 - W * (s[i,k] + t[i,k]), name="Unusable grid cell 1")
            model.addConstr(unusable_gridcell[k]['x'] >= x[i] + w[i] - W * (1 + s[i,k] - t[i,k]), name="Unusable grid cell 2")
            model.addConstr(y[i] >= unusable_gridcell[k]['y'] + unusable_gridcell[k]['h'] + 1 - H * (1 - s[i,k] + t[i,k]), name = "Unusable grid cell 3")
            model.addConstr(unusable_gridcell[k]['y'] >= y[i] + h[i] - H * (2 - s[i,k] - t[i,k]), name = "Unusable grid cell 4")
    # Orientation constraint
    for i in range(n):
        if i!= 0:
            model.addConstr(w[i] == h[i]*((max(obj_params[i]['w_h'])/min(obj_params[i]['w_h']))*orientation[i]
                                          +(min(obj_params[i]['w_h'])/max(obj_params[i]['w_h']))*(1-orientation[i])))
    
    

    # Same orientation for front desks
    model.addConstr(orientation[0]==1)
    model.addConstr(orientation[1]==orientation[2])
    model.addConstr((orientation[1]==1)>>(x[1]==x[2]))

    # Constraints for at least 160 in front of the front desk
    for i in range(n):
        for j in range(n):    
            if [i, j] == [1,0] or [i,j]==[0,1]:
                model.addConstr((orientation[i]==0)>>(x[i] + w[i] + 160 <= x[j] + W * (p[i,j] + q[i,j])))
                model.addConstr((orientation[i]==1)>>(y[i] + h[i] + 160 <= y[j] + H * (1 + p[i,j] - q[i,j])))
                model.addConstr((orientation[i]==0)>>(x[j] + w[j] + 160 <= x[i] + W * (1 - p[i,j] + q[i,j])))
                model.addConstr((orientation[i]==1)>>(y[j] + h[j] + 160 <= y[i] + H * (2 - p[i,j] - q[i,j])))

    # Constraint for object long side againt wall
    for i in range(n):
        for j in range(n):
            if [i, j] == [2,1]:
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
        for i in range(n):
            print(f"Object {i}: x={x[i].X}, y={y[i].X}, w={w[i].X}, h={h[i].X}")
            result.update({i:{'x':x[i].X, 'y':y[i].X, 'w':w[i].X, 'h':h[i].X}})
            for j in range(n):
                if i != j:
                    print(f"p[{i,j}]={p[i,j].X}, q[{i,j}]={q[i,j].X}")
            
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
    total_space = {'width': W, 'height': H}

    # Create a new figure
    plt.figure(figsize=(8, 8))
    matplotlib.rcParams['font.family'] = ['Heiti TC']
    # Plot total space
    plt.gca().add_patch(plt.Rectangle((0, 0), total_space['width'], total_space['height'], fill=None, edgecolor='blue', label='Total Space'))
    object_name = {0: "貨架區",
                    1: "前櫃檯",
                    2: "後櫃檯",
                    3: "WI",
                    4: "6個FF (360x66)",
                    5: "雙溫櫃",
                    6: "單溫櫃",
                    7: "OC",
                    8: "RI",
                    9: "EC",
                    10: "子母櫃",
                    11: "ATM",
                    12: "影印",
                    13: "KIOSK"}
    # Plot each object
    for object_id, object_info in data.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']

        plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=object_name[object_id]))
        plt.text(x + w/2, y + h/2, object_name[object_id], ha='center', va='center', color='red', fontsize=12)

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
    result = layout_opt(obj_params, n, A,W, H, unusable_gridcell, m)
    draw_dxf(result,"20240620_result",W,H)
    layout_plot(result, unusable_gridcell)
    
