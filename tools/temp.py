import ezdxf
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.geometry import LineString

def set_orientation(wall,feasible_area):
    result = []
    for line in wall:
        x1, y1, x2, y2 = line[0], line[1], line[2], line[3]
        if(x1 == x2): # 直線 -- 東西
            point = Point(x1-1, (y1+y2)/2)
            if(y1 > y2):
                tmp = y1
                y1 = y2
                y2 = tmp
            ### record
            if(feasible_area.contains(point)):
                result.append({'orientation': 'east', 'orien_id':[1,0,0,0], 'location':x1, 'range':[y1,y2]})
            else:
                result.append({'orientation': 'west', 'orien_id':[0,1,0,0], 'location':x1, 'range':[y1,y2]})

        else: # 橫線 -- 南北
            point = Point((x1+x2)/2, y1-1)
            if(x1 > x2):
                tmp = x1
                x1 = x2
                x2 = tmp
            if(feasible_area.contains(point)):
                result.append({'orientation': 'north', 'orien_id':[0,0,0,1], 'location':y1, 'range':[x1,x2]})
            else:
                result.append({'orientation': 'south', 'orien_id':[0,0,1,0], 'location':y1, 'range':[x1,x2]})
             
    return result

def split_polygon_to_rectangles(polygon):
    left, bottom, right, top = polygon.bounds
    y_coords = sorted(set([bottom, top] + [y for _, y in polygon.exterior.coords]))
    rectangles = []

    for i in range(len(y_coords) - 1):
        y1, y2 = y_coords[i], y_coords[i + 1]
        strip = box(left, y1, right, y2).intersection(polygon)

        if strip.is_empty:
            continue

        if strip.geom_type == 'Polygon':
            strips = [strip]
        elif strip.geom_type == 'MultiPolygon' or strip.geom_type == 'GeometryCollection':
            strips = [geom for geom in strip.geoms if geom.geom_type == 'Polygon']
        else:
            strips = []

        for strip in strips:
            x_coords = sorted(set([left, right] + [x for x, _ in strip.exterior.coords]))

            for j in range(len(x_coords) - 1):
                x1, x2 = x_coords[j], x_coords[j + 1]
                rectangle = box(x1, y1, x2, y2).intersection(strip)

                if not rectangle.is_empty and rectangle.geom_type == 'Polygon':
                    rectangles.append(rectangle)

    return rectangles

def change_line_to_poly(feasible_area):
    ########## 針對線段進行排序
    result = []
    ### 選定初始點(終點)
    start_x, start_y = feasible_area[0][0],feasible_area[0][1] # 直接選定第一條線段
    result.append((feasible_area[0][0],feasible_area[0][1])) # 第一條線段起點
    result.append((feasible_area[0][2],feasible_area[0][3])) # 第一條線段終點
    
    check_set = np.zeros(len(feasible_area))
    check_set[0] = 1 # 表示已經使用過此線段
    
    closed_area = False ### 確保圍成封閉線段
    
    ### 延著目前座標位置繞行可行解區域一圈形成封閉區域
    while (closed_area == False):
        
        ### 目前座標位置
        search_x = result[len(result)-1][0]
        search_y = result[len(result)-1][1]
        
        ### 檢查是否完成封閉區域(目前座標位置 = 起始點)
        if(search_x == start_x and search_y == start_y):
            closed_area = True
        
        if(closed_area == True):
            break
            
        ### 找下一個 point
        for index,line in enumerate(feasible_area):
            if(check_set[index] == 0): #還沒放
                if(line[0]==search_x and line[1]==search_y):
                    result.append((line[2],line[3]))
                    check_set[index] = 1 
                elif(line[2]==search_x and line[3]==search_y):
                    result.append((line[0],line[1]))
                    check_set[index] = 1 

    ##### 排序完成後 轉換成多邊形
    poly_feasible = Polygon(result)
    
    return(poly_feasible)
    
def get_empty_area(poly_feasible,min_x,max_x,min_y,max_y):
    poly_max = Polygon([(min_x, min_x), (min_x, max_y), (max_x, max_y), (max_x, min_y)])
    poly_empty = poly_max.difference(poly_feasible)
    polygons_empty = list(poly_empty.geoms)
    rectangles_empty = []
    for polygon in polygons_empty:
        if len(polygon.exterior.coords) != 5: # 4個頂點 + 1(頭尾重複一次)
            polygon_split = split_polygon_to_rectangles(polygon)
            for poly in polygon_split:
                rectangles_empty.append(poly)
        else:
            rectangles_empty.append(polygon)
    return rectangles_empty

def adjust_range(data,min_x,min_y):
    for tmp in data:
        tmp[0] = round(tmp[0] - min_x)
        tmp[1] = round(tmp[1] - min_y)
        tmp[2] = round(tmp[2] - min_x)
        tmp[3] = round(tmp[3] - min_y)
    return data

def check_region(x,y,min_x,max_x,min_y,max_y):
    if( x < min_x):
        min_x = x
    if( x > max_x):
        max_x = x
    if( y < min_y):
        min_y = y
    if( y > max_y):
        max_y = y
    return(min_x,max_x,min_y,max_y)

def get_line(entity):
    x1 = round(entity.dxf.start[0],2)
    y1 = round(entity.dxf.start[1],2)
    x2 = round(entity.dxf.end[0],2)
    y2 = round(entity.dxf.end[1],2)
    result = [x1,y1,x2,y2]
    return result

def get_different_layer_line(doc):
    feasible_area = []
    wall = []
    door = []
    min_x = 100000
    max_x = -100000
    min_y = 100000
    max_y = -100000
    for entity in doc.entities:
        ### 確認目標Layer
        if(entity.dxf.layer == 'feasible_area'):
            ### 讀取線段資訊
            x1,y1,x2,y2 = get_line(entity)
            feasible_area.append([x1,y1,x2,y2])
            
            #### 更新邊界範圍
            min_x,max_x,min_y,max_y = check_region(x1,y1,min_x,max_x,min_y,max_y)
            min_x,max_x,min_y,max_y = check_region(x2,y2,min_x,max_x,min_y,max_y)

        elif(entity.dxf.layer == 'solid_wall' or entity.dxf.layer == 'window'):
            wall.append(get_line(entity))
            
        elif(entity.dxf.layer == 'door'):
            ### 讀取線段資訊       
            door.append(get_line(entity))

    ### 範圍調整        
    feasible_area = adjust_range(feasible_area,min_x,min_y)
    wall = adjust_range(wall,min_x,min_y)
    door = adjust_range(door,min_x,min_y)
    min_x,max_x = round(min_x-min_x),round(max_x-min_x)
    min_y,max_y = round(min_y-min_y),round(max_y-min_y)

    return feasible_area,wall,door,min_x,max_x,min_y,max_y

##### 確認牆面方位
def set_orientation(wall,feasible_area):
    result = []
    for line in wall:
        x1, y1, x2, y2 = line[0], line[1], line[2], line[3]
        if(x1 == x2): # 直線 -- 東西
            point = Point(x1-1, (y1+y2)/2)
            if(y1 > y2):
                tmp = y1
                y1 = y2
                y2 = tmp
            ### record
            if(feasible_area.contains(point)):
                result.append({'orientation': 'east', 'orien_id':[1,0,0,0], 'location':x1, 'range':[y1,y2]})
            else:
                result.append({'orientation': 'west', 'orien_id':[0,1,0,0], 'location':x1, 'range':[y1,y2]})

        else: # 橫線 -- 南北
            point = Point((x1+x2)/2, y1-1)
            if(x1 > x2):
                tmp = x1
                x1 = x2
                x2 = tmp
            if(feasible_area.contains(point)):
                result.append({'orientation': 'north', 'orien_id':[0,0,0,1], 'location':y1, 'range':[x1,x2]})
            else:
                result.append({'orientation': 'south', 'orien_id':[0,0,1,0], 'location':y1, 'range':[x1,x2]})
             
    return result

def feasible_area(doc):
    doc = ezdxf.readfile(doc)
    feasible_area,wall,door,min_x,max_x,min_y,max_y = get_different_layer_line(doc)
    
    poly_feasible = change_line_to_poly(feasible_area)
    rectangles_empty = get_empty_area(poly_feasible,min_x,max_x,min_y,max_y)
    wall = set_orientation(wall,poly_feasible)
    door = set_orientation(door,poly_feasible)

    unusable_gridcell = []
    for polygon in rectangles_empty:
        ### 紀錄empty座標位置(左、下、右、上)
        left, bottom, right, top = polygon.bounds
        left, bottom, right, top = int(left), int(bottom), int(right), int(top)
        ### 紀錄位置(x,y)、寬(w)、高(h)
        unusable_gridcell.append({'type':'empty_area','x': left, 'y': bottom, 'w': right - left, 'h': top - bottom})
    return unusable_gridcell,min_x,max_x,min_y,max_y,poly_feasible,wall,door


def front_door(door_data):

    # Find the dictionary with the largest 'range' difference
    max_diff = -float('inf')
    selected_dict = None
    for item in door_data:
        range_diff = abs(item['range'][1] - item['range'][0])
        if range_diff > max_diff:
            max_diff = range_diff
            selected_dict = item

    if selected_dict:
        # Extract information from the selected dictionary
        orientation = selected_dict['orientation']
        location = selected_dict['location']
        range_min, range_max = selected_dict['range']
        
        if orientation in ['north', 'south']:
            # Y-axis is 'location', X-axis is the range
            coordinates = [(range_min, location), (range_max, location)]
        elif orientation in ['east', 'west']:
            # X-axis is 'location', Y-axis is the range
            coordinates = [(location, range_min), (location, range_max)]

        # Create a LineString object
        line = LineString(coordinates)
        print(f"LineString: {line}")
    else:
        print("No valid dictionary found.")
    return(line)
    
if __name__ == "__main__":
    doc = 'revise.dxf'
    unusable_gridcell,min_x,max_x,min_y,max_y,poly_feasible,wall,door = feasible_area(doc)

    ### 創建新圖
    fig, ax = plt.subplots()

    ### 放置物件區域
    ax.add_patch(plt.Rectangle((0, 0), max_x, max_y, edgecolor='black', facecolor='none'))

    ### 繪製 empty area
    for cell in unusable_gridcell:
        x,y = cell['x'], cell['y']
        width, height =  cell['w'], cell['h']
        ax.add_patch(plt.Rectangle((x,y), width, height, edgecolor='black', facecolor='black'))

    ### 設定x,y軸名稱、標題
    ax.set_title('Area with Feasible Area')
    ax.set_xlabel('Width')
    ax.set_ylabel('Height')

    ### 座標範圍
    ax.set_xlim(0, max_x)
    ax.set_ylim(0, max_y)

    ### 顯示圖形
    plt.show()