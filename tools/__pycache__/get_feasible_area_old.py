import ezdxf
import re
import matplotlib.pyplot as plt
import numpy as np

from shapely.geometry import Point, LineString, box
from shapely.geometry import Polygon,MultiPoint  



def check_region(x,y, min_x, max_x, min_y, max_y):

    if( x < min_x):
        min_x = x
    if( x > max_x):
        max_x = x
    if( y < min_y):
        min_y = y
    if( y > max_y):
        max_y = y
    return(min_x,max_x,min_y,max_y)

def feasible_area_adjust(doc):
    min_x = 100000
    max_x = 0
    min_y = 100000
    max_y = 0
    # 擷取feasible_area線段
    feasible_range = []
    for entity in doc.entities:
    # 確認目標Layer
        if (entity.dxf.layer == 'feasible_area'):
            # 讀取線段資訊        
            x1 = round(entity.dxf.start[0],2)
            y1 = round(entity.dxf.start[1],2)
            x2 = round(entity.dxf.end[0],2)
            y2 = round(entity.dxf.end[1],2)
            feasible_range.append([x1,y1,x2,y2])
            
            # 更新邊界範圍
            min_x, max_x, min_y, max_y = check_region(x1,y1, min_x, max_x, min_y, max_y)
            min_x, max_x, min_y, max_y = check_region(x2,y2, min_x, max_x, min_y, max_y)

    # 調整範圍
    for tmp in feasible_range:
        tmp[0] = round(tmp[0] - min_x)
        tmp[1] = round(tmp[1] - min_y)
        tmp[2] = round(tmp[2] - min_x)
        tmp[3] = round(tmp[3] - min_y)

    min_x,max_x = round(min_x-min_x),round(max_x-min_x)
    min_y,max_y = round(min_y-min_y),round(max_y-min_y)


    return feasible_range, min_x, max_x, min_y, max_y

####### 利用shaply尋找需要挖掉的區域
##### 將feasible_area轉換成shapely的Polygon形式
def sort_line(feasible_area):
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
    return (result)
##### 切割多邊形 確保為矩形
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


def feasible_area(doc):
    doc = ezdxf.readfile(doc)
    feasible_range, min_x, max_x, min_y, max_y = feasible_area_adjust(doc)
    sort_feasible_area = sort_line(feasible_range)
    ##### 建立最外圍矩形可行解區域
    poly_max = Polygon([(min_x, min_x), (min_x, max_y), (max_x, max_y), (max_x, min_y)])
    ##### 建立需被挖掉的非可行解區域(最大矩形 - 可行解區域)
    poly_feasible = Polygon(sort_feasible_area)
    poly_empty = poly_max.difference(poly_feasible) # poly_max - poly_feasible

    polygons_empty = list(poly_empty.geoms)
    ####### 確保所有被挖掉的非可行解區域由多個矩形組成
    rectangles_empty = []
    for polygon in polygons_empty:
        if len(polygon.exterior.coords) != 5: # 4個頂點 + 1(頭尾重複一次)
            polygon_split = split_polygon_to_rectangles(polygon)
            for poly in polygon_split:
                rectangles_empty.append(poly)
        else:
            rectangles_empty.append(polygon)

    unusable_gridcell = {}
    count = 0

    for polygon in rectangles_empty:
        ### 紀錄empty座標位置(左、下、右、上)
        left, bottom, right, top = polygon.bounds
        left, bottom, right, top = int(left), int(bottom), int(right), int(top)
        ### 紀錄位置(x,y)、寬(w)、高(h)
        unusable_gridcell[count] = {'x': left, 'y': bottom, 'w': right - left, 'h': top - bottom}
        count += 1
    print(unusable_gridcell, min_x, max_x, min_y, max_y, poly_feasible)
    return unusable_gridcell, min_x, max_x, min_y, max_y, poly_feasible

if __name__ == "__main__":
    feasible_area('/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/revise.dxf')