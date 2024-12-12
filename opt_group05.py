import matplotlib.pyplot as plt
from shapely.geometry import Polygon, box, LineString, MultiLineString, Point
import time
import matplotlib.patches as patches
import matplotlib
from tools import get_feasible_area
from tools import coordinate_flipping as flip
from tools import get_feasible_area
from shapely import affinity
import re
from shapely.ops import unary_union
import opt_group0
import dxf_to_dict_processor
import opt_group0102

def create_preplaced_polygons(unusable_gridcells):
    return [box(cell['x'], cell['y'], cell['x'] + cell['w'], cell['y'] + cell['h']) 
            for cell in unusable_gridcells.values()]

def calculate_edge_lengths(edges):
    lengths = {}
    for edge in edges:
        lengths[edge] = edge.length
    return lengths

# Function to slice a LineString into specific and remaining parts
def slice_line_string(line_strings, specific_line):
    for line in line_strings:
        if line.intersects(specific_line):
            # Get the overlapping (intersection) part
            overlap = line.intersection(specific_line)
            if isinstance(overlap, Point):
                continue  # or handle differently if needed

            # Get the remaining part of the line after removing the specific_line
            remaining = line.difference(specific_line)
            
            # Return the overlap and remaining parts as a list
            if isinstance(remaining, MultiLineString):
                line_strings.remove(line)
                line_strings.extend([overlap] + list(remaining.geoms))
                return line_strings
            elif remaining.is_empty:
                line_strings.remove(line)
                line_strings.extend([overlap])
                return line_strings
            else:
                line_strings.remove(line)
                line_strings.extend([overlap, remaining])
                return line_strings
    return None  # No intersecting line found

def rearrange_linestrings_to_polygon(linestrings):
    # Start with the first LineString
    polygon_order = [linestrings.pop(0)]
    
    # While there are still linestrings left
    while linestrings:
        # Get the last LineString in the ordered list
        last_line = polygon_order[-1]

        last_end = last_line.coords[-1]  # End point of the last line
        
        # Find the next LineString whose start point matches the last end point
        for i, line in enumerate(linestrings):
            if line.coords[0] == last_end:
                # Add this LineString to the ordered list
                polygon_order.append(line)
                # Remove it from the list of remaining lines
                linestrings.pop(i)
                break
        else:
            raise ValueError("Could not find a matching LineString to form a polygon")

    # Ensure the polygon is closed
    if polygon_order[-1].coords[-1] != polygon_order[0].coords[0]:
        raise ValueError("The provided LineStrings do not form a closed polygon")

    return polygon_order

def find_edges_next_to_door(specified_segment, edges):
    edges = slice_line_string(edges, specified_segment)
    # Reorder the list: move the next item to the front, and shift the previous ones to the back
    edges = rearrange_linestrings_to_polygon(edges)
    for i, edge in enumerate(edges):
        if edge == specified_segment or edge.reverse() == specified_segment:
            edges = edges[i+1:] + edges[:i]
    edges1 = edges
    edges2 = list(reversed(edges))
    
    return edges1, edges2

def check_two_consecutive_short_edges(chain):
    """Check if the first two edges in the chain are both shorter than 150."""
    if len(chain) >= 3:  # Ensure there are at least two edges in the chain
        if chain[0].length < 200 and chain[1].length < 200 and chain[2].length <200:
            return True
    return False

def define_orientation(obj,poly_feasible):
    ### 門前至少10cm
    if(obj['w']>obj['h']): ### 橫著擺 面南北
        point = Point(obj['x'] + obj['w']/2, obj['y']-10)
        if(poly_feasible.contains(point)):
            obj_orientation = 'north'
        else:
            obj_orientation = 'south'
    else: ### 直著擺 面東西
        point = Point(obj['x']-10, obj['y'] + obj['h']/2)
        if(poly_feasible.contains(point)):
            obj_orientation = 'east'
        else:
            obj_orientation = 'west'
    return obj_orientation

def place_object_along_wall(obj_params, edges, preplaced_polygons,  specified_segment, room_polygon, space_min_x, space_min_y, space_max_x, space_max_y, door_opening_space, unusable_gridcell, unusable_gridcell0):
    rectangles= [params['w_h'] for params in obj_params.values() if params['group'] == 0.5]
    # random.shuffle(rectangles)
    rectangles = sorted(rectangles, key=lambda x: max(x), reverse=True)
    poly_order = [LineString([room_polygon.exterior.coords[i], room_polygon.exterior.coords[i+1]])
            for i in range(len(room_polygon.exterior.coords) - 1)]
    # Calculate lengths of each edge
    edges1, edges2 = find_edges_next_to_door(specified_segment, poly_order)
    if check_two_consecutive_short_edges(edges1):
        sorted_edges = edges1
    else:
        sorted_edges = edges2
    # Initialize available segments for each edge
    available_segments = {edge: [edge] for edge in sorted_edges}
    # Union of pre-placed polygons
    preplaced_union = unary_union(preplaced_polygons)

    # Find the closest segment to the specified segment

    placements = []
    placement_with_door = []
    for edge in available_segments:
        print(f'Placing on {edge}')
        new_segments = []
        placed_rect = []
        x1, y1 = edge.coords[0]
        x2, y2 = edge.coords[1]            
        if x1 == x2:  # Vertical edge
            print('1')
            for rect_width, rect_height in rectangles:
                placed = False
                # print(f'Trying to place rectangle: {[rect_width, rect_height]}...')
                long_side = max(rect_width, rect_height)
                short_side = min(rect_width, rect_height)
                if long_side <= abs(y2 - y1):
                    print('2')
                    # Try to place the rectangle along the vertical segment
                    min_y = min(y1, y2)
                    max_y = max(y1, y2)
                    for i in range(int(min_y), int(max_y - long_side) + 1):
                        start_y = i
                        rect1 = box(x1+1, start_y, x1 + short_side+1, start_y + long_side)
                        rect_with_door1 = box(x1, start_y, x1 + short_side + door_opening_space, start_y + long_side)
                        rect2 = box(x1 - short_side-1, start_y, x1-1, start_y + long_side)
                        rect_with_door2 = box(x1 - short_side - door_opening_space, start_y, x1, start_y + long_side)
                        if room_polygon.contains(rect_with_door1) and not rect1.intersects(preplaced_union) and all(not rect_with_door1.intersects(p) for p in placements):
                            print('3')
                            placements.append(rect1)
                            placement_with_door.append(rect_with_door1)
                            placed = True
                            break
                        elif room_polygon.contains(rect_with_door2) and not rect2.intersects(preplaced_union) and all(not rect_with_door2.intersects(p) for p in placements):
                            print('4')
                            placements.append(rect2)
                            placement_with_door.append(rect_with_door2)
                            placed = True
                            break 
                if placed:
                    print('5')
                    placed_rect.append([rect_width, rect_height])
                    rectangles = [i for i in rectangles if i not in placed_rect]
                if not placed:
                    print('6')
                    rectangles = [i for i in rectangles if i not in placed_rect]
                    # print(f'New list: {rectangles}')
                    # print('Moving on to the next rectangle...')
                    break

        elif y1 == y2:  # Horizontal edge
            print('7')
            min_x = min(x1, x2)
            max_x = max(x1, x2)
            for rect_width, rect_height in rectangles:
                # print(f'Trying to place rectangle: {[rect_width, rect_height]}...')
                placed = False
                long_side = max(rect_width, rect_height)
                short_side = min(rect_width, rect_height)
                print(f'Placing rectangle: [{rect_width}, {rect_height}]')
                if long_side <= abs(x2 - x1):
                    print('8')
                    # Try to place the rectangle along the horizontal segment
                    for i in range(int(min_x), int(max_x - long_side) + 1):
                        start_x = i
                        rect1 = box(start_x, y1+1, start_x + long_side, y1 + short_side+1)
                        rect_with_door1 = box(start_x, y1+1, start_x + long_side, y1 + short_side + door_opening_space)
                        rect2 = box(start_x, y1 - short_side-1, start_x + long_side, y1-1)
                        rect_with_door2 = box(start_x, y1 - short_side - door_opening_space-1, start_x + long_side, y1)
                        if room_polygon.contains(rect_with_door1) and not rect1.intersects(preplaced_union) and all(not rect_with_door1.intersects(p) for p in placements):
                            print('9')
                            placements.append(rect1)
                            placement_with_door.append(rect_with_door1)
                            placed = True
                            break
                        elif room_polygon.contains(rect_with_door2) and not rect2.intersects(preplaced_union) and all(not rect_with_door2.intersects(p) for p in placements):
                            print('10')
                            placements.append(rect2)
                            placement_with_door.append(rect_with_door2)
                            placed = True
                            break           
                if placed:
                    print('11')
                    # print('Rectangle plcaed!')
                    placed_rect.append([rect_width, rect_height])
                    rectangles = [i for i in rectangles if i not in placed_rect]
                if not placed:
                    print('12')
                    rectangles = [i for i in rectangles if i not in placed_rect]
                    # print(f'New list: {rectangles}')
                    # print('Moving on to the next rectangle...')
                    break
            # print(f'Placed rectangls: {placed_rect}')
            if not rectangles:
                print('13')
                rectangles = [i for i in rectangles if i not in placed_rect]
                break
        if rectangles:
            print('Moving on to the next edge...')
            continue
        if not rectangles:
            print('All rectangles placed!')
            break
    
    placement_with_door = create_dict_from_polygons(placement_with_door, obj_params)
    unusable_gridcell1 = {}
    values = list(unusable_gridcell.values()) + list(unusable_gridcell0.values())+list(placement_with_door.values())
    unusable_gridcell1 = {i: values[i] for i in range(len(values))}
    placements_dict = create_dict_from_polygons(placements, obj_params)
    max_key = max(unusable_gridcell0.keys())
    for key, values in placements_dict.items():
        max_key += 1
        placements_dict[key]['type'] = 'objects'
        placements_dict[key]['orientation'] = define_orientation(values,room_polygon)
        unusable_gridcell0[max_key] = values
    return placements, placements_dict, unusable_gridcell1


# Function to create dictionary from list of polygons
def create_dict_from_polygons(polygons, obj_params):
    rect_dict = {}
    for i, poly in enumerate(polygons):
        if poly == 0:
            break
        min_x, min_y, max_x, max_y = poly.bounds
        rect_dict[i] = {
            'x': min_x,
            'y': min_y,
            'w': max_x - min_x,
            'h': max_y - min_y
        }

    for id, object in rect_dict.items():
        for _, obj in obj_params.items():
            if max(object['w'],object['h']) == max(obj['w_h']) and min(object['w'],object['h'])==min(obj['w_h']):
                rect_dict[id]['name'] = obj['name']
    return rect_dict

if __name__ == '__main__':
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/revise_v1.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/九如東寧_可.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/岡山竹東_可.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/潭子新大茂_可.dxf'
    doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/六甲水林.dxf'
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
    
    result_0, counter_placement, unusable_gridcell0, available_segments = opt_group0.counter_placements(unusable_gridcell_dict, poly_feasible, obj_params, COUNTER_SPACING, LINEUP_SPACING, DOOR_PLACEMENT, DOOR_ENTRY, min_x, max_x, min_y, max_y)
    result_0102, unusable_gridcell0102 = opt_group0102.baseline_placements(obj_params, unusable_gridcell, min_x, max_x, min_y, max_y, wall, door, result_0, counter_placement, unusable_gridcell0, available_segments, DOOR_placement)
    preplaced_polygons = create_preplaced_polygons(unusable_gridcell0102)
    placements_polygon, result_05, unusable_gridcell05 = place_object_along_wall(obj_params, available_segments, preplaced_polygons, DOOR_PLACEMENT, poly_feasible, min_x, min_y, max_x, max_y, OPENDOOR_SPACING, unusable_gridcell_dict, unusable_gridcell0102)
    # print(result)
    
    # Plotting
    fig, ax = plt.subplots()

    # Plot the room polygon
    x, y = poly_feasible.exterior.xy
    ax.plot(x, y, color='blue', linewidth=2, label='Room')

    # Plot the pre-placed rectangles
    for cell in unusable_gridcell0.values():
        rect = box(cell['x'], cell['y'], cell['x'] + cell['w'], cell['y'] + cell['h'])
        x, y = rect.exterior.xy
        ax.plot(x, y, color='grey', linewidth=2, linestyle='--', label='Pre-placed')

    # Plot the placed rectangles
    for rect in placements_polygon:
        x, y = rect.exterior.xy
        ax.plot(x, y, color='red', linewidth=2)

    ax.set_aspect('equal')
    plt.legend()
    plt.show()
