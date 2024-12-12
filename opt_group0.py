import matplotlib.pyplot as plt
from shapely.geometry import box, LineString, Point
from shapely.ops import unary_union
from tools import get_feasible_area
import dxf_to_dict_processor
# 抓牆面的問題
def create_preplaced_polygons(unusable_gridcells):
    return [box(cell['x'], cell['y'], cell['x'] + cell['w'], cell['y'] + cell['h']) 
            for cell in unusable_gridcells.values()]

def calculate_edge_lengths(edges):
    lengths = {}
    for edge in edges:
        lengths[edge] = edge.length
    return lengths

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

def find_closest_segment(specified_segment, edges):
    closest_segment = None
    min_distance = float('inf')
    x1, y1 = specified_segment.coords[0]
    x2, y2 = specified_segment.coords[1]
    specified_seg_orientation = 0
    if x1 == x2:
        specified_seg_orientation = 1
    else:
        pass
    for edge in edges:
        edge_orientation = 0
        if edge != specified_segment or edge != specified_segment.reverse():
            distance = specified_segment.distance(edge)
            if edge.length >= 598:
                x1, y1 = edge.coords[0]
                x2, y2 = edge.coords[1]
                if x1 == x2:  # Vertical edge
                    edge_orientation = 1
                else:
                    pass
                if specified_seg_orientation != edge_orientation:
                    if distance < min_distance:
                        min_distance = distance
                        closest_segment = edge

    edges = rearrange_linestrings_to_polygon(edges)
    for i, edge in enumerate(edges):
        if edge.intersection(closest_segment) or edge.intersection(closest_segment.reverse()):
            edge_starting_from_cloest_segment = edges[i-1:] + edges[:i]
    return edge_starting_from_cloest_segment, edge_orientation

def place_counter_along_wall(room_polygon, rectangles, preplaced_polygons, specified_segment, min_x, max_x, min_y, max_y):
    # Extract the edges of the polygon
    edges = [LineString([room_polygon.exterior.coords[i], room_polygon.exterior.coords[i+1]])
             for i in range(len(room_polygon.exterior.coords) - 1)]
    
    sorted_edges, edge_orientation = find_closest_segment(specified_segment, edges)
    
    # Initialize available segments for each edge
    available_segments = {edge: [edge] for edge in sorted_edges}
    
    # Union of pre-placed polygons
    preplaced_union = unary_union(preplaced_polygons)
    
    
    placements = []
    for edge in available_segments:
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
                        rect1 = box(x1, start_y, x1 + short_side, start_y + long_side)
                        rect2 = box(x1 - short_side, start_y, x1, start_y + long_side)
                        if room_polygon.contains(rect1) and not rect1.intersects(preplaced_union) and all(not rect1.intersects(p) for p in placements):
                            print('3')
                            placements.append(rect1)
                            placed = True
                            break
                        elif room_polygon.contains(rect2) and not rect2.intersects(preplaced_union) and all(not rect2.intersects(p) for p in placements):
                            print('4')
                            placements.append(rect2)
                            placed = True
                            break 
                if placed:
                    print('5')
                    placed_rect.append((rect_width, rect_height))
                    rectangles = [i for i in rectangles if i not in placed_rect]
                    placed_edge = edge
                    break
                if not placed:
                    print('6')
                    rectangles = [i for i in rectangles if i not in placed_rect]
                    # print(f'New list: {rectangles}')
                    # print('Moving on to the next rectangle...')
                    break

        elif y1 == y2:  # Horizontal edge
            print('7')
            for rect_width, rect_height in rectangles:
                # print(f'Trying to place rectangle: {[rect_width, rect_height]}...')
                placed = False
                long_side = max(rect_width, rect_height)
                short_side = min(rect_width, rect_height)
                if long_side <= abs(x2 - x1):
                    print('8')
                    # Try to place the rectangle along the horizontal segment
                    min_x = min(x1, x2)
                    max_x = max(x1, x2)
                    for i in range(int(min_x), int(max_x - long_side) + 1):
                        start_x = i
                        rect1 = box(start_x, y1, start_x + long_side, y1 + short_side)
                        rect2 = box(start_x, y1 - short_side, start_x - long_side, y1)
                        if room_polygon.contains(rect1) and not rect1.intersects(preplaced_union) and all(not rect1.intersects(p) for p in placements):
                            print('9')
                            placements.append(rect1)
                            placed = True
                            break
                        elif room_polygon.contains(rect2) and not rect2.intersects(preplaced_union) and all(not rect2.intersects(p) for p in placements):
                            print('10')
                            placements.append(rect2)
                            placed = True
                            break                    
                if placed:
                    print('11')
                    # print('Rectangle plcaed!')
                    available_segments[edge] = [seg for seg in new_segments if seg.length > 0]
                    placed_rect.append((rect_width, rect_height))
                    rectangles = [i for i in rectangles if i not in placed_rect]
                    placed_edge = edge
                    break
                if not placed:
                    print('12')
                    rectangles = [i for i in rectangles if i not in placed_rect]
                    # print(f'New list: {rectangles}')
                    # print('Moving on to the next rectangle...')
                    break
            
            if not rectangles:
                print('13')
                rectangles = [i for i in rectangles if i not in placed_rect]
                # print(f'New list: {rectangles}')
                break
            
        if rectangles:
            print('Moving on to the next edge...')
            continue
        if not rectangles:
            print('All rectangles placed!')
            break
    x1, y1 = placed_edge.coords[0]
    x2, y2 = placed_edge.coords[1]
    point1 = Point(x1-1, (y1+y2)/2)
    point2 = Point((x1+x2)/2, y1-1)
    if x1 == x2:
        if point1.within(room_polygon):
            counter_placement = 'east'
        else:
            counter_placement = 'west'
    elif y1 == y2:
        if point2.within(room_polygon):
            counter_placement = 'north'
        else:
            counter_placement = 'south'
    return placements, counter_placement, available_segments

def counter_placements(unusable_gridcell, room_polygon, obj_params, counter_space, lineup_space, specified_segment, preplaced, min_x, max_x, min_y, max_y):
    rectangles = []
    for id , object in obj_params.items():
        if object['name'] == '後櫃檯':
            w1 = max(object['w_h'])
            h1 = min(object['w_h'])
        elif object['name'] == '前櫃檯':
            w2 = max(object['w_h'])
            h2 = min(object['w_h'])
        else:
            pass
    rectangles.append((w1, h1 + h2 + counter_space + lineup_space))

    # Create saved space for door entry
    preplaced_polygons = create_preplaced_polygons(preplaced)

    placements, counter_placement, available_segments = place_counter_along_wall(room_polygon, rectangles, preplaced_polygons, specified_segment, min_x, max_x, min_y, max_y)

    # Extract the bounds of the polygon (minx, miny, maxx, maxy)
    minx, miny, maxx, maxy = placements[0].bounds

    # Calculate width and height
    width = maxx - minx
    height = maxy - miny

    # Create the dictionary
    counter_area = {
        'x': minx,
        'y': miny,
        'w': width,
        'h': height
    }
    x1, y1 = specified_segment.coords[0]
    x2, y2 = specified_segment.coords[1]
    point1 = Point(x1-1, (y1+y2)/2)
    point2 = Point((x1+x2)/2, y1-1)
    if x1 == x2:
        if point1.within(room_polygon):
            door_placement = 'east'
        else:
            door_placement = 'west'
    elif y1 == y2:
        if point2.within(room_polygon):
            door_placement = 'north'
        else:
            door_placement = 'south'

    counter_result = {}
    if counter_placement =='east' and door_placement == 'north':
        # 後櫃檯
        counter_result.update({0:{'x':counter_area['x']+counter_area['w']-h1, 'y':counter_area['y'], 'w':h1, 'h':w1, 'name':'後櫃檯'}})
        # 前櫃檯
        counter_result.update({1:{'x':counter_area['x']+lineup_space, 'y':counter_area['y']+(w1-w2), 'w':h2, 'h':w2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        # 排隊空間
        unusable_gridcell0.update({2:{'x':counter_area['x'], 'y':counter_area['y']+(w1-w2), 'w':lineup_space, 'h':w2}})
        # 兩個櫃檯間距
        unusable_gridcell0.update({3:{'x':counter_area['x']+lineup_space+h2, 'y':counter_area['y'], 'w':counter_space, 'h':w1}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+lineup_space, 'y':counter_area['y']+(w1-w2)-90, 'w':h2, 'h':90}})
    elif counter_placement =='east' and door_placement == 'south':
        counter_result.update({0:{'x':counter_area['x']+counter_area['w']-h1, 'y':counter_area['y'], 'w':h1, 'h':w1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+lineup_space, 'y':counter_area['y'], 'w':h2, 'h':w2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x'], 'y':counter_area['y'], 'w':lineup_space, 'h':w2}})
        unusable_gridcell0.update({3:{'x':counter_area['x']+lineup_space+h2, 'y':counter_area['y'], 'w':counter_space, 'h':w1}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+lineup_space, 'y':counter_area['y']+w2, 'w':h2, 'h':90}})
    elif counter_placement =='west' and door_placement == 'north':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y'], 'w':h1, 'h':w1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+h1+counter_space, 'y':counter_area['y']+(w1-w2), 'w':h2, 'h':w2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x']+h1+counter_space+h2, 'y':counter_area['y']+(w1-w2), 'w':lineup_space, 'h':w2}})
        unusable_gridcell0.update({3:{'x':counter_area['x']+h1, 'y':counter_area['y'], 'w':counter_space, 'h':w1}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+h1+counter_space, 'y':counter_area['y']+(w1-w2)-90, 'w':h2, 'h':90}})
    elif counter_placement =='west' and door_placement == 'south':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y'], 'w':h1, 'h':w1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+h1+counter_space, 'y':counter_area['y'], 'w':h2, 'h':w2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x']+counter_area['w']-lineup_space, 'y':counter_area['y'], 'w':lineup_space, 'h':w2}})
        unusable_gridcell0.update({3:{'x':counter_area['x']+h1, 'y':counter_area['y'], 'w':counter_space, 'h':w1}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+h1+counter_space, 'y':counter_area['y']+w2, 'w':h2, 'h':90}})
        
    elif counter_placement =='north' and door_placement == 'west':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y']+counter_area['h']-h1, 'w':w1, 'h':h1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x'], 'y':counter_area['y']+lineup_space, 'w':w2, 'h':h2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x'], 'y':counter_area['y'], 'w':w2, 'h':lineup_space}})
        unusable_gridcell0.update({3:{'x':counter_area['x'], 'y':counter_area['y']+lineup_space+h2, 'w':w1, 'h':counter_space}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+w2, 'y':counter_area['y']+lineup_space, 'w':90, 'h':h2}})
    elif counter_placement =='north' and door_placement == 'east':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y']+counter_area['h']-h1, 'w':w1, 'h':h1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+(w1-w2), 'y':counter_area['y']+lineup_space, 'w':w2, 'h':h2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x']+(w1-w2), 'y':counter_area['y'], 'w':w2, 'h':lineup_space}})
        unusable_gridcell0.update({3:{'x':counter_area['x'], 'y':counter_area['y']+lineup_space+h2, 'w':w1, 'h':counter_space}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+(w1-w2)-90, 'y':counter_area['y']+lineup_space, 'w':90, 'h':h2}})
    elif counter_placement =='south' and door_placement == 'west':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y'], 'w':w1, 'h':h1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x'], 'y':counter_area['y']+h1+counter_space, 'w':w2, 'h':h2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x'], 'y':counter_area['y']+counter_area['h']-lineup_space, 'w':w2, 'h':lineup_space}})
        unusable_gridcell0.update({3:{'x':counter_area['x'], 'y':counter_area['y']+h1, 'w':w1, 'h':counter_space}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+w2, 'y':counter_area['y']+h1+counter_space, 'w':90, 'h':h2}})
    elif counter_placement =='south' and door_placement == 'east':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y'], 'w':w1, 'h':h1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+(w1-w2), 'y':counter_area['y']+h1+counter_space, 'w':w2, 'h':h2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x']+(w1-w2), 'y':counter_area['y']+counter_area['h']-lineup_space, 'w':w2, 'h':lineup_space}})
        unusable_gridcell0.update({3:{'x':counter_area['x'], 'y':counter_area['y']+h1, 'w':w1, 'h':counter_space}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+(w1-w2)-90, 'y':counter_area['y']+h1+counter_space, 'w':90, 'h':h2}})
    
    elif counter_placement =='east':
        counter_result.update({0:{'x':counter_area['x']+counter_area['w']-h1, 'y':counter_area['y'], 'w':h1, 'h':w1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+lineup_space, 'y':counter_area['y'], 'w':h2, 'h':w2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x'], 'y':counter_area['y'], 'w':lineup_space, 'h':w2}})
        unusable_gridcell0.update({3:{'x':counter_area['x']+lineup_space+h2, 'y':counter_area['y'], 'w':counter_space, 'h':w1}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+lineup_space, 'y':counter_area['y']+w2, 'w':h2, 'h':90}})
    elif counter_placement =='west':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y'], 'w':h1, 'h':w1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x']+h1+counter_space, 'y':counter_area['y']+(w1-w2), 'w':h2, 'h':w2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x']+h1+counter_space+h2, 'y':counter_area['y']+(w1-w2), 'w':lineup_space, 'h':w2}})
        unusable_gridcell0.update({3:{'x':counter_area['x']+h1, 'y':counter_area['y'], 'w':counter_space, 'h':w1}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+h1+counter_space, 'y':counter_area['y']+(w1-w2)-90, 'w':h2, 'h':90}})
    elif counter_placement =='north':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y']+counter_area['h']-h1, 'w':w1, 'h':h1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x'], 'y':counter_area['y']+lineup_space, 'w':w2, 'h':h2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x'], 'y':counter_area['y'], 'w':w2, 'h':lineup_space}})
        unusable_gridcell0.update({3:{'x':counter_area['x'], 'y':counter_area['y']+lineup_space+h2, 'w':w1, 'h':counter_space}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+w2, 'y':counter_area['y']+lineup_space, 'w':90, 'h':h2}})  
    elif counter_placement =='south':
        counter_result.update({0:{'x':counter_area['x'], 'y':counter_area['y'], 'w':w1, 'h':h1, 'name':'後櫃檯'}})
        counter_result.update({1:{'x':counter_area['x'], 'y':counter_area['y']+h1+counter_space, 'w':w2, 'h':h2, 'name':'前櫃檯'}})
        unusable_gridcell0 = counter_result.copy()
        unusable_gridcell0.update({2:{'x':counter_area['x'], 'y':counter_area['y']+counter_area['h']-lineup_space, 'w':w2, 'h':lineup_space}})
        unusable_gridcell0.update({3:{'x':counter_area['x'], 'y':counter_area['y']+h1, 'w':w1, 'h':counter_space}})
        unusable_gridcell0.update({4:{'x':counter_area['x']+w2, 'y':counter_area['y']+h1+counter_space, 'w':90, 'h':h2}})
    unusable_gridcell_output = unusable_gridcell.copy()
    max_key = max(unusable_gridcell_output .keys())
    for key, value in unusable_gridcell0.items():
        max_key += 1
        if 'name' in unusable_gridcell0[key]:
            unusable_gridcell0[key]['type'] = 'objects'
        else:
            unusable_gridcell0[key]['type'] = 'aisle'
        unusable_gridcell_output [max_key] = value
    unusable_gridcell_output[max_key+1] = preplaced[0]
    # print(preplaced)
    # print(preplaced[0])
    # print("testtttt")
    # print(unusable_gridcell)
    # print("testenddddd")
    # values = list(unusable_gridcell0.values())+list(preplaced.values())
    # unusable_gridcell0 = {}
    # unusable_gridcell0 = {i: values[i] for i in range(len(values))}
    return  counter_result, counter_placement, unusable_gridcell_output , available_segments

if __name__ == '__main__':
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/revise_v1.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/九如東寧_可.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/岡山竹東_可.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/潭子新大茂_可.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/六甲水林.dxf'
    #doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/竹南旺大埔.dxf'
    doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/§jµo¶Xµo_™≈_0909.dxf'
    unusable_gridcell, unusable_gridcell_dict, min_x, max_x, min_y, max_y, poly_feasible, wall, door, frontdoor = get_feasible_area.feasible_area(doc)

    SPACE_WIDTH,SPACE_HEIGHT= max_x-min_x+1, max_y-min_y+1
    AISLE_SPACE = 100
    COUNTER_SPACING = 110
    OPENDOOR_SPACING = 110
    LINEUP_SPACING = 160
    
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
        12: {'group':1,'w_h': [80,55], 'fixed_wall': 'any', 'name':'KIOSK'}
    }

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

    counter_result, counter_placement, unusable_gridcell_1, available_segments = counter_placements(unusable_gridcell_dict, poly_feasible, obj_params, COUNTER_SPACING, LINEUP_SPACING, DOOR_PLACEMENT, DOOR_ENTRY, min_x, max_x, min_y, max_y)
    # Plotting
    fig, ax = plt.subplots()

    # Plot the room polygon
    x, y = poly_feasible.exterior.xy
    ax.plot(x, y, color='blue', linewidth=2, label='Room')

    # Plot the pre-placed rectangles
    for cell in unusable_gridcell_1.values():
        rect = box(cell['x'], cell['y'], cell['x'] + cell['w'], cell['y'] + cell['h'])
        x, y = rect.exterior.xy
        ax.plot(x, y, color='grey', linewidth=2, linestyle='--', label='Pre-placed')

    # Plot the placed rectangles
    for rect in counter_result.values():
        rect = box(rect['x'], rect['y'], rect['x'] + rect['w'], rect['y'] + rect['h'])
        x, y = rect.exterior.xy
        ax.plot(x, y, color='red', linewidth=2)

    # Highlight the specified and closest segments
    x, y = DOOR_PLACEMENT.xy
    ax.plot(x, y, color='green', linewidth=2, linestyle='--', label='Specified Segment')

    ax.set_aspect('equal')
    plt.legend()
    
    ### 存檔
    plt.savefig('part1_layout.png', dpi=300, bbox_inches='tight')
    
    plt.show()
