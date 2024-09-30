# delete connectivity constraint
import matplotlib.pyplot as plt
import matplotlib
from tools import get_feasible_area
from tools import get_feasible_area
from dxf_tools import dxf_manipulation
import re
import opt_group0
from shapely.geometry import LineString, Point
import opt_group0
import opt_group0102
import opt_group05
import opt_group08
import opt_group1
import opt_group2
import opt_shelf
import dxf_to_dict_processor




def layout_plot(obj_params, result0, result0102, result1, result2, shelf_placement, unusable_gridcell):
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
    
    data = result0102

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
        shelf_name = f"{int(shelf_placement[i]['w'])}x{int(shelf_placement[i]['h'])}"
        object_name.update({i:shelf_name})
    
    # Plot each object
    for object_id, object_info in data.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']
        '''
        if object_id ==0:
        
            plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=object_name[object_id]))
            print(f'The area of shelf area = {w}x{h}')
            plt.text(x + w/2, y + h/2, object_name[object_id], ha='center', va='center', color='red', fontsize=12)
            
            pass
          
        else:
            plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=object_info['name']))
            plt.text(x + w/2, y + h/2, object_info['name'], ha='center', va='center', color='red', fontsize=12)  
        '''
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
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/revise_v1.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/九如東寧_可.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/岡山竹東_可.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/潭子新大茂_可.dxf'
    doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/六甲水林.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/竹南旺大埔.dxf'
    unusable_gridcell,unusable_gridcell_dict, min_x, max_x, min_y, max_y, poly_feasible, wall, door, frontdoor = get_feasible_area.feasible_area(doc)
    print(poly_feasible)
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
    point1 = Point(x1-1, (y1+y2)/2)
    point2 = Point((x1+x2)/2, y1-1)
    if x1 == x2:
        if point1.within(poly_feasible):
            DOOR_ENTRY = {0:{'x':x1-200, 'y':min(y1,y2), 'w':200, 'h':max(y1,y2)-min(y1,y2)}}
            DOOR_placement = 'east'
        else:
            DOOR_ENTRY = {0:{'x':x1, 'y':min(y1,y2), 'w':200, 'h':max(y1,y2)-min(y1,y2)}}
            DOOR_placement = 'west'
            
    elif y1 == y2:
        if point2.within(poly_feasible):
            DOOR_ENTRY = {0:{'x':min(x1,x2), 'y':y1-200, 'w':max(x1,x2)-min(x1,x2), 'h':200}}
            DOOR_placement = 'north'
        else:
            DOOR_ENTRY = {0:{'x':min(x1,x2), 'y':y1, 'w':max(x1,x2)-min(x1,x2), 'h':200}}
            DOOR_placement = 'south'
    #Define the parameters and variables
    obj_params = {
        0: {'group':2,'w_h': [SPACE_WIDTH,SPACE_HEIGHT], 'fixed_wall': 'none', 'name':'貨架區'},
        1: {'group':0,'w_h': [465,66], 'fixed_wall': 'none', 'name':'前櫃檯'},
        2: {'group':0,'w_h': [598,66], 'fixed_wall': 'any', 'name':'後櫃檯'},
        3: {'group':0.1,'w_h': [365,270], 'fixed_wall': 'any', 'name':'WI', 'num':1, 'aisle': 120}, 
        4: {'group':0.2,'w_h': [90,66], 'fixed_wall': 'none', 'name':'D_T', 'num':2, 'aisle': 120},
        5: {'group':0.2,'w_h': [90,66], 'fixed_wall': 'none', 'name':'S_T', 'num':2, 'aisle': 120},
        6: {'group':0.2,'w_h': [90,66], 'fixed_wall': 'none', 'name':'OC', 'num':2, 'aisle': 120},
        7: {'group':0.1,'w_h': [310,225], 'fixed_wall': 'any', 'name':'RI', 'num':1, 'aisle': 120},
        8: {'group':1,'w_h': [95,59], 'fixed_wall': 'any', 'name':'EC'},
        9: {'group':1,'w_h': [190,90], 'fixed_wall': 'any', 'name':'子母櫃'},
        10: {'group':0.8,'w_h': [100,85], 'fixed_wall': 'any', 'name':'ATM'},
        11: {'group':0.5,'w_h': [83,64], 'fixed_wall': 'any', 'name':'影印'},
        12: {'group':0.5,'w_h': [80,55], 'fixed_wall': 'any', 'name':'KIOSK'}
    }

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
    
    priority_shelves = [7, 8, 9,10,11, 13, 14, 15, 16, 17]

    
    result_0, counter_placement, unusable_gridcell0, available_segments = opt_group0.counter_placements(poly_feasible, obj_params, COUNTER_SPACING, LINEUP_SPACING, DOOR_PLACEMENT, DOOR_ENTRY, min_x, max_x, min_y, max_y)
    result_0102, unusable_gridcell0102 = opt_group0102.baseline_placements(obj_params, unusable_gridcell, min_x, max_x, min_y, max_y, wall, door, result_0, counter_placement, unusable_gridcell0, available_segments, DOOR_placement)
    preplaced_polygons = opt_group05.create_preplaced_polygons(unusable_gridcell0102)
    print(preplaced_polygons)
    _, result_05, unusable_gridcell05 = opt_group05.place_object_along_wall(obj_params, available_segments, preplaced_polygons, DOOR_PLACEMENT, poly_feasible, min_x, min_y, max_x, max_y, OPENDOOR_SPACING, unusable_gridcell_dict, unusable_gridcell0102)
    preplaced_polygons = opt_group08.create_preplaced_polygons(unusable_gridcell05)
    _, result_08, unusable_gridcell08 = opt_group08.place_object_along_wall(obj_params, available_segments, preplaced_polygons,DOOR_PLACEMENT, poly_feasible, min_x, min_y, max_x, max_y, OPENDOOR_SPACING, unusable_gridcell_dict, unusable_gridcell05)
    preplaced_polygons = opt_group1.create_preplaced_polygons(unusable_gridcell08)
    _, result_1, unusable_gridcell1 = opt_group1.place_object_along_wall(obj_params, available_segments, preplaced_polygons,poly_feasible, min_x, min_y, max_x, max_y, OPENDOOR_SPACING, unusable_gridcell_dict, unusable_gridcell08)
    result_2, shelf_area, shelf_id = opt_group2.middle_object(obj_params, AISLE_SPACE, SPACE_WIDTH, SPACE_HEIGHT, unusable_gridcell1)
    result_2.pop(shelf_id)
    shelf_placement, unusable_gridcell2 = opt_shelf.shelf_opt(shelf_area, unusable_gridcell1, counter_placement, DOOR_placement, shelf_params, priority_shelves, AISLE_SPACE)
    #shelf_placement = {}
    wall_values = list(result_0.values()) + list(result_05.values())+ list(result_08.values())
    result_0 = {i: wall_values[i] for i in range(len(wall_values))}
    values = list(result_0.values())+list(result_1.values()) +list(result_2.values())
    result = {i: values[i] for i in range(len(values))}
    dxf_manipulation.draw_dxf(result,feasible)
    layout_plot(obj_params, result_0, result_0102, result_1, result_2, shelf_placement,unusable_gridcell_dict)
