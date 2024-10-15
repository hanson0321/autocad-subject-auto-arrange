from ortools.sat.python import cp_model
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib
from tools import get_feasible_area
from tools import coordinate_flipping as flip
from tools import get_feasible_area
import dxf_to_dict_processor
import re

def layout_with_numeric_value(shelf_params, priority_shelves, SPACE_WIDTH, SPACE_HEIGHT, AISLE_SPACE):
    # Create the model
    model = cp_model.CpModel()

    num_shelf = len(shelf_params)
    unusable_gridcell = {0: {'x': 0, 'y': 0, 'w': 470, 'h': 176}}
    num_unusable_cells = len(unusable_gridcell)

    # Define variables
    select = [model.NewBoolVar(f'select_{i}') for i in range(num_shelf)]
    x = [model.NewIntVar(0, SPACE_WIDTH, f'x_{i}') for i in range(num_shelf)]
    y = [model.NewIntVar(0, SPACE_HEIGHT, f'y_{i}') for i in range(num_shelf)]
    w = [model.NewIntVar(0, SPACE_WIDTH, f'w_{i}') for i in range(num_shelf)]
    h = [model.NewIntVar(0, SPACE_HEIGHT, f'h_{i}') for i in range(num_shelf)]

    # Non-overlapping variables (analogous to p and q)
    p, q, s , t = {}, {}, {}, {}

    for i in range(num_shelf):
        for j in range(num_shelf):
            if i != j:
                p[(i, j)] = model.NewBoolVar(f'p_{i}_{j}')
                q[(i, j)] = model.NewBoolVar(f'q_{i}_{j}')
        for k in range(num_unusable_cells):
            s[(i, k)] = model.NewBoolVar(f"s_{i}_{k}")
            t[(i, k)] = model.NewBoolVar(f"t_{i}_{k}")



    # Unusable grid cell constraint
    for i in range(num_shelf):
        for k in range(num_unusable_cells):
            model.Add(x[i] >= unusable_gridcell[k]['x']+ unusable_gridcell[k]['w'] + 1 - SPACE_WIDTH * (s[i,k] + t[i,k])).OnlyEnforceIf(select[i])
            model.Add(unusable_gridcell[k]['x'] >= x[i] + w[i] - SPACE_WIDTH * (1 + s[i,k] - t[i,k])).OnlyEnforceIf(select[i])
            model.Add(y[i] >= unusable_gridcell[k]['y'] + unusable_gridcell[k]['h'] + 1 - SPACE_HEIGHT * (1 - s[i,k] + t[i,k])).OnlyEnforceIf(select[i])
            model.Add(unusable_gridcell[k]['y'] >= y[i] + h[i] - SPACE_HEIGHT * (2 - s[i,k] - t[i,k])).OnlyEnforceIf(select[i])
    
    # Boundary constraints
    for i in range(num_shelf):
        model.Add(x[i] + w[i] <= SPACE_WIDTH).OnlyEnforceIf(select[i])
        model.Add(y[i] + h[i]<= SPACE_HEIGHT - 60).OnlyEnforceIf(select[i])
    
    # Non-intersecting constraints
    for i in range(num_shelf):
        for j in range(num_shelf):
            if i != j:
                model.Add(x[i] + w[i] + AISLE_SPACE <= x[j] + SPACE_WIDTH * (p[i,j] + q[i,j]) + SPACE_WIDTH * (1 - select[j]))
                model.Add(y[i] + h[i] + AISLE_SPACE <= y[j] + SPACE_HEIGHT * (1 + p[i,j] - q[i,j]) + SPACE_HEIGHT * (1 - select[j]))
                model.Add(x[j] + w[j] + AISLE_SPACE <= x[i] + SPACE_WIDTH * (1 - p[i,j] + q[i,j]) + SPACE_WIDTH * (1 - select[i]))
                model.Add(y[j] + h[j] + AISLE_SPACE <= y[i] + SPACE_HEIGHT * (2 - p[i,j] - q[i,j]) + SPACE_HEIGHT * (1 - select[i]))

    # Width and height constraints
    for i in range(num_shelf):
        model.Add(w[i] == max(shelf_params[i]['w_h']))
        model.Add(h[i] == min(shelf_params[i]['w_h']))
    
    # Priority constraint
    model.Add(sum(select[i] for i in priority_shelves) >= 1)
    
    # Summation constraints
    model.Add(sum(select[i] * shelf_params[i]['amount'] for i in range(num_shelf)) >= 25)
    model.Add(sum(select[i] * shelf_params[i]['amount'] for i in range(num_shelf)) <= 35)
    
    # Objective function: Maximize priority shelf selection while minimizing distance
    model.Maximize(
        sum(select[i] * (10 if i in priority_shelves else 3) for i in range(num_shelf))
        - 0.01 * sum(x[i] + y[i] for i in range(num_shelf))
    )

    # Create the solver
    solver = cp_model.CpSolver()

    # Solve the model
    status = solver.Solve(model)


    # Collect results
    result = {}
    tmp = 0
    if status == cp_model.OPTIMAL:
        for i in range(num_shelf):
            if solver.BooleanValue(select[i]):
                result[i] = {
                    'x': solver.Value(x[i]),
                    'y': solver.Value(y[i]),
                    'w': solver.Value(w[i]),
                    'h': solver.Value(h[i]),
                    'number': shelf_params[i]['amount'],
                    'name': shelf_params[i]['name']
                }
                tmp+=1
                # print(f"Shelf {shelf_params[i]['name']}: x={x[i].X}, y={y[i].X}, w={w[i].X}, h={h[i].X}, number={shelf_params[i]['amount']}")
        tmp+=1
        result.update({tmp:{'x':0,'y':0,'w':360,'h':66,'name':'FF'}})
    else:
        print("Model is infeasible")


    return result


def layout_plot(result):

    # Create a new figure
    plt.figure(figsize=(8, 8))
    matplotlib.rcParams['font.family'] = ['Heiti TC']
    # Plot opt_group0
    
    data = result

    # Plot total space
    plt.gca().add_patch(plt.Rectangle((0, 0), SPACE_WIDTH, SPACE_HEIGHT, fill=None, edgecolor='blue', label='Total Space'))

    # Plot each object
    for object_id, object_info in data.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']

        plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=object_info['name']))
        plt.text(x + w/2, y + h/2, object_info['name'], ha='center', va='center', color='red', fontsize=12)


    # Set plot limits and labels
    plt.xlim(0, SPACE_WIDTH)
    plt.ylim(0,SPACE_HEIGHT)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Space Layout')

    # Show plot
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()
    

if __name__ == '__main__':
    doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/岡山竹東_可.dxf'
    unusable_gridcell,unusable_gridcell_dict, min_x, max_x, min_y, max_y, poly_feasible, wall, door, frontdoor = get_feasible_area.feasible_area(doc)
    # Extract points from the input string using regular expression
    points = re.findall(r'\d+\s\d+', str(poly_feasible).replace("POLYGON ", ""))
    # Convert points to tuples of integers
    feasible = [tuple(map(int, point.split())) for point in points]

    SPACE_WIDTH,SPACE_HEIGHT= max_x-min_x+1, max_y-min_y+1
    AISLE_SPACE = 110
    COUNTER_SPACING = 110
    OPENDOOR_SPACING = 110
    LINEUP_SPACING = 160

    layers_to_draw = ['solid_wall', 'window', 'door']
    edge_dictionary = dxf_to_dict_processor.process_dxf(doc, layers_to_draw) 

    # Define the specified segment (e.g., the first edge of the polygon)
    DOOR_PLACEMENT = frontdoor
    # DOOR_PLACEMENT = get_feasible_area.front_door(door)
    # DOOR_PLACEMENT = next(item['edge'] for item in edge_dictionary.values() if item['type'] == 'door')
    
    # Space for door entry
    x1, y1 = DOOR_PLACEMENT.coords[0]
    x2, y2 = DOOR_PLACEMENT.coords[1]
    if x1 == x2:
        if x1 < (min_x+max_x)/2:
            DOOR_ENTRY = {0:{'x':x1, 'y':min(y1,y2), 'w':200, 'h':max(y1,y2)-min(y1,y2)}}
            DOOR_placement = 'west'
        else:
            DOOR_ENTRY = {0:{'x':x1-200, 'y':min(y1,y2), 'w':200, 'h':max(y1,y2)-min(y1,y2)}}
            DOOR_placement = 'east'
    elif y1 == y2:
        if y1 < (min_y+max_y)/2:
            DOOR_ENTRY = {0:{'x':min(x1,x2), 'y':y1, 'w':max(x1,x2)-min(x1,x2), 'h':200}}
            DOOR_placement = 'south'
        else:
            DOOR_ENTRY = {0:{'x':min(x1,x2), 'y':y1-200, 'w':max(x1,x2)-min(x1,x2), 'h':200}}
            DOOR_placement = 'north'
    print(f'DOOR_ENTRY{DOOR_ENTRY}')
    priority_shelves = [7, 8, 9, 10,11, 13, 14, 15, 16, 17]

    shelf_params = {0:{'w_h':[91,78],'amount':2, 'name':'91x78'},
                    1:{'w_h':[132,78],'amount':3, 'name':'132x78'},
                    2:{'w_h':[182,78],'amount':4, 'name':'182x78'},
                    3:{'w_h':[223,78],'amount':5, 'name':'223x78'},
                    4:{'w_h':[273,78],'amount':6, 'name':'273x78'},
                    5:{'w_h':[314,78],'amount':7, 'name':'314x78'},
                    6:{'w_h':[364,78],'amount':8, 'name':'364x78'},
                    7:{'w_h':[405,78],'amount':9, 'name':'405x78'},
                    8:{'w_h':[405,78],'amount':9, 'name':'405x78'},
                    9:{'w_h':[405,78],'amount':9, 'name':'405x78'},
                    10:{'w_h':[405,78],'amount':9, 'name':'405x78'},
                    11:{'w_h':[405,78],'amount':9, 'name':'405x78'},
                    12:{'w_h':[455,78],'amount':10, 'name':'455x78'},
                    13:{'w_h':[496,78],'amount':11, 'name':'496x78'},
                    14:{'w_h':[496,78],'amount':11, 'name':'496x78'},
                    15:{'w_h':[496,78],'amount':11, 'name':'496x78'},
                    16:{'w_h':[496,78],'amount':11, 'name':'496x78'},
                    17:{'w_h':[496,78],'amount':11, 'name':'496x78'},
                    18:{'w_h':[546,78],'amount':12, 'name':'546x78'},
                    19:{'w_h':[587,78],'amount':13, 'name':'587x78'},
                    20:{'w_h':[546,78],'amount':14, 'name':'637x78'},
                    21:{'w_h':[678,78],'amount':15, 'name':'678x78'}}
    result = layout_with_numeric_value(shelf_params,priority_shelves,  1400, 1000, AISLE_SPACE)

    layout_plot(result)
