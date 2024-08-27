# delete connectivity constraint
import matplotlib.pyplot as plt
import matplotlib
from tools import get_feasible_area
from tools import get_feasible_area
from dxf_tools import dxf_manipulation
import re
import opt_group0
from shapely.geometry import LineString
import opt_group0
import opt_group1
import opt_group2
import opt_shelf
import dxf_to_dict_processor




def layout_plot(obj_params, result0, result1, result2, shelf_placement, unusable_gridcell):
    num_objects = len(obj_params)
    # Define total space dimensions
    total_space = {'width': SPACE_WIDTH, 'height': SPACE_HEIGHT}

    # Create a new figure
    plt.figure(figsize=(8, 8))
    matplotlib.rcParams['font.family'] = ['Heiti TC']
    # Plot opt_group0
    
    data = result0

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
    
    
    data = result1
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
    
    # Plot opt_group2
    data = result2
    print(f'result2 = {data}')

    # Plot each object
    for object_id, object_info in data.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']
        if object_info['name'] == '貨架區':

            plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=object_info['name']))
            print(f'The area of shelf area = {w}x{h}')
            plt.text(x + w/2, y + h/2, object_info['name'], ha='center', va='center', color='red', fontsize=12)
            
            #pass
        else:
            plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=object_info['name']))
            plt.text(x + w/2, y + h/2, object_info['name'], ha='center', va='center', color='red', fontsize=12)
    
    # Plot shelf area
    data = shelf_placement

    num_shelf = len(shelf_placement)
    object_name = {}
    for i in range(num_shelf):
        if i ==0:
            shelf_name = 'FF'
            object_name.update({i:shelf_name})
        else:
            shelf_name = f"{int(shelf_placement[i]['w'])}x{int(shelf_placement[i]['h'])}"
            object_name.update({i:shelf_name})
  
    # Plot each object
    for object_id, object_info in data.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']
        
        plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=object_info['name']))
        plt.text(x + w/2, y + h/2, object_info['name'], ha='center', va='center', color='red', fontsize=12)
      
    # Plot obstacle
    # Parameters adaptation
    obstacle_positions = [(unusable_gridcell[k]['x'], unusable_gridcell[k]['y']) for k in unusable_gridcell]
    obstacle_dimensions = [(unusable_gridcell[k]['w'], unusable_gridcell[k]['h']) for k in unusable_gridcell]
    for k, (x_u, y_u) in enumerate(obstacle_positions):
        w_u, h_u = obstacle_dimensions[k]
        plt.gca().add_patch(plt.Rectangle((x_u, y_u), w_u, h_u, fill=None, edgecolor='red', label = 'X'))
        plt.text(x_u + w_u/2, y_u + h_u/2, 'x', ha='center', va='center', color='red', fontsize=8)

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

    doc ='/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/revise_v1.dxf'
    unusable_gridcell, min_x, max_x, min_y, max_y, poly_feasible = get_feasible_area.feasible_area(doc)
    
    # Extract points from the input string using regular expression
    points = re.findall(r'\d+\s\d+', str(poly_feasible).replace("POLYGON ", ""))
    # Convert points to tuples of integers
    feasible = [tuple(map(int, point.split())) for point in points]

    SPACE_WIDTH,SPACE_HEIGHT= max_x-min_x+1, max_y-min_y+1
    AISLE_SPACE = 100
    COUNTER_SPACING = 110
    OPENDOOR_SPACING = 110
    LINEUP_SPACING = 160

    layers_to_draw = ['solid_wall', 'window', 'door']
    edge_dictionary = dxf_to_dict_processor.process_dxf(doc, layers_to_draw) 

    # Define the specified segment (e.g., the first edge of the polygon)
    DOOR_PLACEMENT = next(item['edge'] for item in edge_dictionary.values() if item['type'] == 'door')
    
    # Space for door entry
    x1, y1 = DOOR_PLACEMENT.coords[0]
    x2, y2 = DOOR_PLACEMENT.coords[1]
    if x1 == x2:
        if x1 < (min_x+max_x)/2:
            DOOR_ENTRY = {0:{'x':x1, 'y':min(y1,y2), 'w':200, 'h':max(y1,y2)-min(y1,y2)}}
        else:
            DOOR_ENTRY = {0:{'x':x1-200, 'y':min(y1,y2), 'w':200, 'h':max(y1,y2)-min(y1,y2)}}
    elif y1 == y2:
        if y1 < (min_y+max_y)/2:
            DOOR_ENTRY = {0:{'x':min(x1,x2), 'y':y1, 'w':max(x1,x2)-min(x1,x2), 'h':200}}
        else:
            DOOR_ENTRY = {0:{'x':min(x1,x2), 'y':y1-200, 'w':max(x1,x2)-min(x1,x2), 'h':200}}

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
        12: {'group':1,'w_h': [80,55], 'fixed_wall': 'any', 'name':'KIOSK'},
        13: {'group':1, 'w_h':[170,50],'fixed_wall': 'any','name':'座位1'}
    }
    shelf_spec = [132, 223, 314, 405, 496, 587, 678, 91, 182, 273, 364, 455, 546]
    shelf_height = [78]

    result_0, counter_placement, unusable_gridcell0, available_segments = opt_group0.counter_placements(poly_feasible, obj_params, COUNTER_SPACING, LINEUP_SPACING, DOOR_PLACEMENT, DOOR_ENTRY, min_x, max_x, min_y, max_y)
    preplaced_polygons = opt_group1.create_preplaced_polygons(unusable_gridcell0)
    rectangles= [params['w_h'] for params in obj_params.values() if params['group'] == 1]
    print(rectangles)
    _, result_1, unusable_gridcell1 = opt_group1.place_object_along_wall(obj_params, available_segments, rectangles, preplaced_polygons,poly_feasible, min_x, min_y, max_x, max_y, OPENDOOR_SPACING, unusable_gridcell, unusable_gridcell0)
    result_2, shelf_area, shelf_id = opt_group2.middle_object(obj_params, AISLE_SPACE, SPACE_WIDTH, SPACE_HEIGHT, unusable_gridcell1)
    result_2.pop(shelf_id)
    shelf_placement = opt_shelf.shelf_opt(shelf_area, shelf_spec, shelf_height, counter_placement)
    result = {}
    values = list(result_0.values()) + list(result_1.values()) +list(result_2.values()) + list(shelf_placement.values())
    result = {i: values[i] for i in range(len(values))}
    dxf_manipulation.draw_dxf(result,feasible)
    layout_plot(obj_params, result_0, result_1, result_2, shelf_placement, unusable_gridcell)
