# add unused grid cell contraint
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches

DualReductions = 0
#Define the parameters and variables
obj_params = {
    0: {'w_1': 66, 'w_2': 422, 'h_1': 66, 'h_2': 422, 'connect':[], 'fixed_wall': 'east'},
    1: {'w_1': 66, 'w_2': 658, 'h_1': 66, 'h_2': 658, 'connect':[], 'fixed_wall': 'none'},
    2: {'w_1': 270, 'w_2': 365, 'h_1': 270, 'h_2': 365, 'connect':[], 'fixed_wall': 'none'}, 
    3: {'w_1': 60, 'w_2': 66, 'h_1': 60, 'h_2': 66, 'connect':[], 'fixed_wall': 'none'},
    4: {'w_1': 90, 'w_2': 90, 'h_1': 90, 'h_2': 90, 'connect':[], 'fixed_wall': 'none'},
    5: {'w_1': 225, 'w_2': 310, 'h_1': 225, 'h_2': 310, 'connect':[], 'fixed_wall': 'none'},
    6: {'w_1': 59, 'w_2': 95, 'h_1': 59, 'h_2': 95, 'connect':[], 'fixed_wall': 'none'}
}


unused_grid_cell = {
    0:{'x':0,'y':0,'w':100, 'h':30},
    1:{'x':500,'y':0,'w':150, 'h':50}
}
n = len(obj_params)
m = len(unused_grid_cell)


# Space parameters
W = 1000
H = 1000
A = 60
'''
# Weights
# The ith room positioned to the nearest top left corner
u_1 = 1
# The total absolute distance
u_2 = 1
# The weight of the total approximated area
u_3 = 1
'''
# Fixed object position
fixed_room = 0
x_fixed = 0
y_fixed = 0
T = 0.5
def layout_opt(obj_params, n, T, A, fixed_foom, x_fixed, y_fixed, unused_grid_cell, m):
    # Create a Gurobi model
    start_time = time.time()
    model = gp.Model("layout_generation")
    model.params.NonConvex = 2
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
        for k in range(n):
            s[i, k] = model.addVar(vtype=GRB.BINARY, name=f"s_{i}_{k}")
    t = {}
    for i in range(n):
        for k in range(n):
            t[i, k] = model.addVar(vtype=GRB.BINARY, name=f"t_{i}_{k}")
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
    orientation = {}
    for k in range(n):
        orientation[k] = model.addVar(vtype=GRB.BINARY, name=f"orientation_{k}")
    
    # Set objective
    #model.setObjective(gp.quicksum(w[i]*h[i] for i in range(n)), GRB.MINIMIZE)
    #model.setParam('TimeLimit', 1800)
    total_area = gp.quicksum(w[i] * h[i] for i in range(n))
    coor =gp.quicksum(x[i] + y[i] for i in range(n))
    model.setObjective((coor - total_area), GRB.MINIMIZE)
    # Set constraints

    # Connectivity constraint
    for i in range(n):
        if not obj_params[i]['connect']:
            print(f'No connectivity constraint for object {i}')
        else:
            for j in obj_params[i]['connect']:
                model.addConstr(x[i] + w[i] >= x[j] - W*(p[i,j] + q[i,j]), name="Connectivity Constraint 1")
                model.addConstr(y[j] + h[j] >= y[i] - H*(1 + p[i,j] - q[i,j]), name="Connectivity Constraint 2")
                model.addConstr(x[j] + w[j] >= x[i] - W*(1 - p[i,j] + q[i,j]), name = "Connectivity Constraint 3")
                model.addConstr(y[i] + h[i] >= y[j] - H*(2 - p[i,j] - q[i,j]), name = "Connectivity Constraint 4")
    '''
    # Fixed position constraint
    model.addConstr(x[fixed_foom] == x_fixed)
    model.addConstr(y[fixed_foom] == y_fixed)
    '''
    # Boundary constraints
    for i in range(n):
        model.addConstr(x[i] + w[i] <= W, name="Boundary constraint for x")
        model.addConstr(y[i] + h[i] <= H, name="Boundary constraint for y")
    
    # Fixed border constraint
    for i in range(n):
        if obj_params[i]['fixed_wall'] == 'north':
            model.addConstr(y[i] == 0, name="North border constraint")
        elif obj_params[i]['fixed_wall']== 'south':
            model.addConstr(y[i]+h[i] == H, name="South border constraint")
        elif obj_params[i]['fixed_wall']== 'east':
            model.addConstr(x[i]+w[i] == W, name="East border constraint")
        elif obj_params[i]['fixed_wall']== 'west':
            model.addConstr(x[i] == 0, name="West border constraint")
        else:
            print(f'No fixed wall constraint for object {i}')
    
    # Non-intersecting constraint
    for i in range(n):
        for j in range(n):
            if not obj_params[i]['connect'] and i != j:
                model.addConstr(x[i] + w[i] +A <= x[j] + W * (p[i,j] + q[i,j]), name="Non-intersecting Constraint 1")
                model.addConstr(y[j] + h[j] +A <= y[i] + H * (1 + p[i,j] - q[i,j]), name="Non-intersecting Constraint 2")
                model.addConstr(x[j] + w[j] +A<= x[i] + W * (1 - p[i,j] + q[i,j]), name = "Non-intersecting Constraint 3")
                model.addConstr(y[i] + h[i] +A <= y[j] + H * (2 - p[i,j] - q[i,j]), name = "Non-intersecting Constraint 4")
            elif i!=j:
                model.addConstr(x[i] + w[i] <= x[j] + W * (p[i,j] + q[i,j]), name="Non-intersecting Constraint 1")
                model.addConstr(y[j] + h[j] <= y[i] + H * (1 + p[i,j] - q[i,j]), name="Non-intersecting Constraint 2")
                model.addConstr(x[j] + w[j] <= x[i] + W * (1 - p[i,j] + q[i,j]), name = "Non-intersecting Constraint 3")
                model.addConstr(y[i] + h[i] <= y[j] + H * (2 - p[i,j] - q[i,j]), name = "Non-intersecting Constraint 4")

    
    # Length constraint
    for i in range(n):
        model.addConstr(w[i]==[obj_params[i]['w_1'],obj_params[i]['w_2']] , name="Length Constraint 1")
        model.addConstr(h[i] == [obj_params[i]['h_1'], obj_params[i]['h_2']], name="Height Constraint 2")
        
    # Overlapping constraint
    for i in range(n):
        if not obj_params[i]['connect']:
            print(f'No connectivity constraint for object {i}')
        else:
            for j in obj_params[i]['connect']:
                model.addConstr(0.5*(w[i] + w[j]) >= T + (x[j] - x[i]) - W*(p[i,j] + q[i,j]), name="constraint_18")
                model.addConstr(0.5*(h[i] + h[j]) >= T + (y[j] - y[i]) - H*(2 - p[i,j] - q[i,j]), name="constraint_19")
                model.addConstr(0.5*(w[i] + w[j]) >= T + (x[i] - x[j]) - W*(1 - p[i,j] + q[i,j]), name="constraint_20")
                model.addConstr(0.5*(h[i] + h[j]) >= T + (y[i] - y[j]) - H*(1 + p[i,j] - q[i,j]), name="constraint_21")
    
    # Unused grid cell constraint
    for i in range(n):
        for k in range(m):
            model.addConstr(x[i] >= unused_grid_cell[k]['x']+ unused_grid_cell[k]['w'] + 1 - W * (s[i,k] + t[i,k]), name="Unused grid cell 1")
            model.addConstr(unused_grid_cell[k]['x'] >= x[i] + w[i] - W * (1 + s[i,k] - t[i,k]), name="Unused grid cell 2")
            model.addConstr(y[i] >= unused_grid_cell[k]['y'] + unused_grid_cell[k]['h'] + 1 - H * (1 - s[i,k] + t[i,k]), name = "Unused grid cell 3")
            model.addConstr(unused_grid_cell[k]['y'] >= y[i] + h[i] - H * (2 - s[i,k] - t[i,k]), name = "Unused grid cell 4")

    for i in range(n):
        model.addConstr(w[i] == h[i]*((obj_params[i]['w_1']/obj_params[i]['h_2'])*orientation[i]+(obj_params[i]['w_2']/obj_params[i]['h_1'])*(1-orientation[i])))
    # Optimize the model
    model.optimize()

    end_time = time.time()
    result = {}
    # Print objective value and runtime
    if model.status == GRB.OPTIMAL:
        print(f"Runtime: {end_time - start_time} seconds")
        print("Optimal solution found!")
        for i in range(n):
            print(f"Room {i}: x={x[i].X}, y={y[i].X}, w={w[i].X}, h={h[i].X}")
            result.update({i:{'x':x[i].X, 'y':y[i].X, 'w':w[i].X, 'h':h[i].X}})
        print("Total area:", model.objVal)
        
    elif model.status == GRB.INFEASIBLE:
        print("The problem is infeasible. Review your constraints.")
    else:
        print("No solution found.")
        '''
        model.computeIIS()
        for c in model.getConstrs():
            if c.IISConstr: print(f'\t{c.constrname}: {model.getRow(c)} {c.Sense} {c.RHS}')
        '''
    return result   

def layout_plot(result, unused_grid_cell):
    
    # Define room data
    data = result

    # Define total space dimensions
    total_space = {'width': W, 'height': H}

    # Create a new figure
    plt.figure(figsize=(8, 8))

    # Plot total space
    plt.gca().add_patch(plt.Rectangle((0, 0), total_space['width'], total_space['height'], fill=None, edgecolor='blue', label='Total Space'))

    # Plot each room
    for object_id, object_info in data.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']
        plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=f'object {object_id}'))
        plt.text(x + w/2, y + h/2, f'object {object_id}', ha='center', va='center', color='red', fontsize=8)
    
    # Plot obstacle
    # Parameters adaptation
    obstacle_positions = [(unused_grid_cell[k]['x'], unused_grid_cell[k]['y']) for k in unused_grid_cell]
    obstacle_dimensions = [(unused_grid_cell[k]['w'], unused_grid_cell[k]['h']) for k in unused_grid_cell]
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
    plt.legend()

    # Show plot
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()

if __name__ == '__main__':
    layout_plot(layout_opt(obj_params, n, T, A, fixed_room, x_fixed, y_fixed, unused_grid_cell, m), unused_grid_cell)
