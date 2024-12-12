import matplotlib.pyplot as plt
from shapely.geometry import box, LineString, Point
from shapely.ops import unary_union
# from ortools.sat.python import cp_model
from tools import get_feasible_area
import opt_group0
from ortools.linear_solver import pywraplp
import time

def transform_counter(counter_placement, unusable_gridcell_1):

    for key, value in unusable_gridcell_1.items():
        if value.get('name') == '前櫃檯':
            tmp_x, tmp_y = unusable_gridcell_1[key]['x'], unusable_gridcell_1[key]['y']
            tmp_w, tmp_h = unusable_gridcell_1[key]['w'], unusable_gridcell_1[key]['h']
            unusable_gridcell_1[key]['orientation'] = counter_placement
            unusable_gridcell_1[key]['right'] = tmp_x + tmp_w
            unusable_gridcell_1[key]['top'] = tmp_y + tmp_h
            unusable_gridcell_1[key]['center_2'] = [tmp_x+(tmp_x+tmp_w), tmp_y+(tmp_y+tmp_h)]
            
            ### 定義方向list
            if(counter_placement == 'east'):
                unusable_gridcell_1[key]['orien_id'] = [1,0,0,0]
            elif(counter_placement == 'west'):
                unusable_gridcell_1[key]['orien_id'] = [0,1,0,0]
            elif(counter_placement == 'south'):
                unusable_gridcell_1[key]['orien_id'] = [0,0,1,0]
            else:
                unusable_gridcell_1[key]['orien_id'] = [0,0,0,1]
                
            counter_set = unusable_gridcell_1[key]
        if value.get('name') == '後櫃檯':
            unusable_gridcell_1[key]['orientation'] = counter_placement
    unusable_gridcell_list = list(unusable_gridcell_1.values())

    return unusable_gridcell_list, counter_set

def optimization(objects, objects_for_set_baseline, counter_set, feasible_wall, unusable_gridcell,min_x, max_x, min_y, max_y):
    ##### 建立model
    model = pywraplp.Solver.CreateSolver('SCIP') ### 適用於混整數規劃
    # model = pywraplp.Solver.CreateSolver('GLOP') ### 適用純連續整數之線姓規劃
    # model = cp_model.CpModel() ### 適用於整數規劃

    ##### 決定物件位置
    obj_set = []
    ##### obj_set[0] -> counter # 先沒有
    
    ##### 計算有多少個可以用來當baseline的物件
    # num_baseline = 1 # counter
    # for baseline_obj in objects_for_set_baseline:
    #     ### 若是沒有找到這個baseline物件的資訊會報錯
    #     baseline_index = next(index for index, obj in enumerate(objects) if obj.get('name') == baseline_obj)
    #     num_baseline += objects[baseline_index]['num']
    # print(num_baseline)
    
    ########### 待修
    # WI_id = next(index for index, obj in enumerate(objects) if obj.get('name') == 'WI')
    # RI_id = next(index for index, obj in enumerate(objects) if obj.get('name') == 'RI')
    
    ##### 定義參數 beseline objects
    num_baseline = 1 # counter
    for obj_id, obj in enumerate(objects): # width, height
        if obj['set_type'] == 'baseline_objects':
            for i in range(obj['num']):
                num_baseline += 1
                tmp_obj_set = {}
                tmp_obj_set['index'] = obj_id
                tmp_obj_set['name'] = obj['name']
                tmp_obj_set['aisle'] = obj['aisle']
                tmp_obj_set['x'] = model.NumVar(min_x, max_x, f'obj_{obj_id}_x') # x
                tmp_obj_set['y'] = model.NumVar(min_y, max_y, f'obj_{obj_id}_y') # y
                tmp_obj_set['right'] = model.NumVar(min_x, max_x, f'obj_{obj_id}_right')  # right
                tmp_obj_set['top'] = model.NumVar(min_y, max_y, f'obj_{obj_id}_top')  # top
                tmp_obj_set['orien_id'] = [ model.BoolVar(f'obj_{obj_id}_east'),
                                            model.BoolVar(f'obj_{obj_id}_west'),
                                            model.BoolVar(f'obj_{obj_id}_south'),
                                            model.BoolVar(f'obj_{obj_id}_north')]
                tmp_obj_set['set_wall'] = True
                tmp_obj_set['choose_wall'] = []
                for k in range(len(feasible_wall)):
                    tmp_obj_set['choose_wall'].append(model.BoolVar(f'obj_{obj_id}_set_wall_{k}'))

                obj_set.append(tmp_obj_set)
    
    ##### 定義參數 -- set on baseline objects        
    for obj_id, obj in enumerate(objects): # width, height
        if obj['set_type'] == 'set_objects':    
            for i in range(obj['num']):
                tmp_obj_set = {}
                tmp_obj_set['index'] = obj_id
                tmp_obj_set['name'] = objects[obj_id]['name']
                tmp_obj_set['aisle'] = obj['aisle']
                tmp_obj_set['x'] = model.NumVar(min_x, max_x, f'obj_{obj_id}_{i}_x')  # x
                tmp_obj_set['y'] = model.NumVar(min_y, max_y, f'obj_{obj_id}_{i}_y') # y
                tmp_obj_set['right'] = model.NumVar(min_x, max_x, f'obj_{obj_id}_{i}_right') # right
                tmp_obj_set['top'] = model.NumVar(min_y, max_y, f'obj_{obj_id}_{i}_top')  # top
                tmp_obj_set['orien_id'] = [ model.BoolVar(f'obj_{obj_id}_{i}_east'),
                                            model.BoolVar(f'obj_{obj_id}_{i}_west'),
                                            model.BoolVar(f'obj_{obj_id}_{i}_south'),
                                            model.BoolVar(f'obj_{obj_id}_{i}_north') ]
                tmp_obj_set['set_wall'] = False
                # 選擇 counter、WI、RI 延伸出的 baseline 做放置
                tmp_obj_set['choose_baseline'] = [model.BoolVar(f'obj_{obj_id}_{i}_SetOn_Counter')]
                for k in range(len(objects_for_set_baseline)):
                    tmp_obj_set['choose_baseline'].append( model.BoolVar(f'obj_{obj_id}_{i}_SetOn_{obj_set[k]["name"]}'))
                tmp_obj_set['center_2'] = [ model.NumVar(0, max_x*2, f'obj_{obj_id}_{i}_center*2_x'),
                                            model.NumVar(0, max_y*2, f'obj_{obj_id}_{i}_center*2_y') ]
                tmp_obj_set['distance'] = [ model.NumVar(0, max_x*2, f'obj_{obj_id}_{i}_distance*2_x'),
                                            model.NumVar(0, max_y*2, f'obj_{obj_id}_{i}_distance*2_y') ]
                obj_set.append(tmp_obj_set)
        
    ### 物件right,top = x,y + w,h
    for obj in obj_set:
        ### 靠南北 right = x + w,  靠東西 right = x + h
        model.Add(obj['right'] == obj['x'] + objects[obj['index']]['w']*(1-obj['orien_id'][0]-obj['orien_id'][1]) + objects[obj['index']]['h']*(obj['orien_id'][0]+obj['orien_id'][1]))
    #     model.Add(obj['right'] <= max_x)
        ### 靠南北 top = y + h, 靠東西 top = y + w
        model.Add(obj['top'] == obj['y'] + objects[obj['index']]['h']*(1-obj['orien_id'][0]-obj['orien_id'][1]) + objects[obj['index']]['w']*(obj['orien_id'][0]+obj['orien_id'][1]))
    #     model.Add(obj['top'] <= max_y)

    ### 物件center_x = (x + right)/2 , center_y = (y + top)/2
    for obj in obj_set:
        if(obj['set_wall']==False):
            ### 靠南北 right = x + w,  靠東西 right = x + h
            model.Add(obj['center_2'][0] == obj['x'] + obj['right'])
            model.Add(obj['center_2'][1] == obj['y'] + obj['top'])

    ##### 物件靠牆設定
    for obj in obj_set:
        ### 物件只會有一面靠牆
        model.Add(sum(obj['orien_id']) == 1)
        
        ##### 決定物件靠哪一面牆 WI/RI
        if(obj['set_wall'] == True):
            ### 選擇一面靠牆
            model.Add(sum(obj['choose_wall']) == 1)
            
            ### 物件和靠的牆 方位需要一致
            for cell_id, cell in enumerate(feasible_wall):
                cond1 = model.BoolVar(f"orien_id1_{objects[obj['index']]['name']}_wall_{cell_id}")
                cond2 = model.BoolVar(f"orien_id1_{objects[obj['index']]['name']}_wall_{cell_id}")
                
                model.Add(obj['choose_wall'][cell_id] >= False - (1 - cond1) * 1e6) # 不是靠這面牆
                model.Add(obj['choose_wall'][cell_id] <= False + (1 - cond1) * 1e6) # 不是靠這面牆
                model.Add(sum(obj['orien_id'][i]*cell['orien_id'][i] for i in range(4)) >= 1 - (1 - cond2) * 1e6) # 是的話 方位相同
                model.Add(sum(obj['orien_id'][i]*cell['orien_id'][i] for i in range(4)) <= 1 + (1 - cond2) * 1e6) # 是的話 方位相同
                        
                model.Add(cond1 + cond2 >= 1)
                
            for cell_id, cell in enumerate(feasible_wall):
                cond1 = model.BoolVar(f"orien_id1_{objects[obj['index']]['name']}_wall_{cell_id}")
                cond2 = model.BoolVar(f"orien_id2_{objects[obj['index']]['name']}_wall_{cell_id}")
                cond3 = model.BoolVar(f"orien_id3_{objects[obj['index']]['name']}_wall_{cell_id}")
                cond4 = model.BoolVar(f"orien_id4_{objects[obj['index']]['name']}_wall_{cell_id}")
                cond5 = model.BoolVar(f"orien_id5_{objects[obj['index']]['name']}_wall_{cell_id}")
                
                model.Add(obj['choose_wall'][cell_id] >= False - (1 - cond1) * 1e6) # 不是靠這面牆
                model.Add(obj['choose_wall'][cell_id] <= False + (1 - cond1) * 1e6) # 不是靠這面牆
                # 是的話 靠牆面value = location
                model.Add(obj['right'] >= cell['location'] + 10000*(cell['orien_id'][0]-1) - (1 - cond2) * 1e6)
                model.Add(obj['x'] >= cell['location'] + 10000*(cell['orien_id'][1]-1) - (1 - cond3) * 1e6)
                model.Add(obj['y'] >= cell['location'] + 10000*(cell['orien_id'][2]-1) - (1 - cond4) * 1e6)
                model.Add(obj['top'] >= cell['location'] + 10000*(cell['orien_id'][3]-1) - (1 - cond5) * 1e6)
                model.Add(obj['right'] <= cell['location'] + 10000*(cell['orien_id'][0]-1) + (1 - cond2) * 1e6)
                model.Add(obj['x'] <= cell['location'] + 10000*(cell['orien_id'][1]-1) + (1 - cond3) * 1e6)
                model.Add(obj['y'] <= cell['location'] + 10000*(cell['orien_id'][2]-1) + (1 - cond4) * 1e6)
                model.Add(obj['top'] <= cell['location'] + 10000*(cell['orien_id'][3]-1) + (1 - cond5) * 1e6)
                        
                model.Add(cond1 + cond2 + cond3 + cond4 + cond5 >= 1)
                ### 待修 -- 靠牆range要在牆面的range內
        
        ##### 決定物件靠哪一條 baseline(counter/WI/RI) OC/單溫/雙溫
        else: ### obj['set_wall'] == False
            ### 選擇一條 baseline
            model.Add(sum(obj['choose_baseline']) == 1)
            
            ##### counter       
            ### 確實落在baseline上面 
            cond1 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnCounter_1")
            cond2 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnCounter_2")
            cond3 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnCounter_3")
            cond4 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnCounter_4")
            cond5 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnCounter_5")

            model.Add(obj['choose_baseline'][0] >= False - (1 - cond1) * 1e6) # 不是在counter的baseline上
            model.Add(obj['choose_baseline'][0] <= False + (1 - cond1) * 1e6) # 不是在counter的baseline上
            # 是的話 counter靠牆的另一面value = 物件同一面的value
            model.Add(obj['right'] >= (counter_set['right'] + 10000*(counter_set['orien_id'][1]-1)) - (1 - cond2) * 1e6)
            model.Add(obj['x'] >= counter_set['x'] + 10000*(counter_set['orien_id'][0]-1) - (1 - cond3) * 1e6)
            model.Add(obj['y'] >= counter_set['y'] + 10000*(counter_set['orien_id'][3]-1) - (1 - cond4) * 1e6)
            model.Add(obj['top'] >= counter_set['top'] + 10000*(counter_set['orien_id'][2]-1) - (1 - cond5) * 1e6)
            model.Add(obj['right'] <= (counter_set['right'] + 10000*(counter_set['orien_id'][1]-1)) + (1 - cond2) * 1e6)
            model.Add(obj['x'] <= counter_set['x'] + 10000*(counter_set['orien_id'][0]-1) + (1 - cond3) * 1e6)
            model.Add(obj['y'] <= counter_set['y'] + 10000*(counter_set['orien_id'][3]-1) + (1 - cond4) * 1e6)
            model.Add(obj['top'] <= counter_set['top'] + 10000*(counter_set['orien_id'][2]-1) + (1 - cond5) * 1e6)

            model.Add(cond1 + cond2 + cond3 + cond4 + cond5 >= 1)
            
            ### 方向相同
            cond1 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnCounter_orien_1")
            cond2 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnCounter_orien_2")
            cond3 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnCounter_orien_3")
            cond4 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnCounter_orien_4")
            cond5 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnCounter_orien_5")
            
            model.Add(obj['choose_baseline'][0] >= False - (1 - cond1) * 1e6) # 不是在counter的baseline上
            model.Add(obj['choose_baseline'][0] <= False + (1 - cond1) * 1e6) # 不是在counter的baseline上
            # 是的話 靠的方向要一樣
            model.Add(obj['orien_id'][0] + counter_set['orien_id'][0] >= 2 - (1 - cond2) * 1e6)
            model.Add(obj['orien_id'][1] + counter_set['orien_id'][1] >= 2 - (1 - cond3) * 1e6)
            model.Add(obj['orien_id'][2] + counter_set['orien_id'][2] >= 2 - (1 - cond4) * 1e6)
            model.Add(obj['orien_id'][3] + counter_set['orien_id'][3] >= 2 - (1 - cond5) * 1e6)
            model.Add(obj['orien_id'][0] + counter_set['orien_id'][0] <= 2 + (1 - cond2) * 1e6)
            model.Add(obj['orien_id'][1] + counter_set['orien_id'][1] <= 2 + (1 - cond3) * 1e6)
            model.Add(obj['orien_id'][2] + counter_set['orien_id'][2] <= 2 + (1 - cond4) * 1e6)
            model.Add(obj['orien_id'][3] + counter_set['orien_id'][3] <= 2 + (1 - cond5) * 1e6)

            model.Add(cond1 + cond2 + cond3 + cond4 + cond5 >= 1)
            
            ###########################################################################
            
            ##### 其他
            for k in range(num_baseline-1):
                ### 確實落在baseline上面
                cond1 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnWI_1")
                cond2 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnWI_2")
                cond3 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnWI_3")
                cond4 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnWI_4")
                cond5 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnWI_5")

                model.Add(obj['choose_baseline'][k+1] >= False - (1 - cond1) * 1e6) # 不是在WI的baseline上
                model.Add(obj['choose_baseline'][k+1] <= False + (1 - cond1) * 1e6) # 不是在WI的baseline上
                # 是的話 counter靠牆的另一面value = 物件同一面的value
                model.Add(obj['right'] >= obj_set[k]['right'] + 10000*(obj_set[k]['orien_id'][1]-1) - (1 - cond2) * 1e6)
                model.Add(obj['x'] >= obj_set[k]['x'] + 10000*(obj_set[k]['orien_id'][0]-1) - (1 - cond3) * 1e6)
                model.Add(obj['y'] >= obj_set[k]['y'] + 10000*(obj_set[k]['orien_id'][3]-1) - (1 - cond4) * 1e6)
                model.Add(obj['top'] >= obj_set[k]['top'] + 10000*(obj_set[k]['orien_id'][2]-1) - (1 - cond5) * 1e6)
                model.Add(obj['right'] <= obj_set[k]['right'] + 10000*(obj_set[k]['orien_id'][1]-1) + (1 - cond2) * 1e6)
                model.Add(obj['x'] <= obj_set[k]['x'] + 10000*(obj_set[k]['orien_id'][0]-1) + (1 - cond3) * 1e6)
                model.Add(obj['y'] <= obj_set[k]['y'] + 10000*(obj_set[k]['orien_id'][3]-1) + (1 - cond4) * 1e6)
                model.Add(obj['top'] <= obj_set[k]['top'] + 10000*(obj_set[k]['orien_id'][2]-1) + (1 - cond5) * 1e6)

                model.Add(cond1 + cond2 + cond3 + cond4 + cond5 >= 1)
            
                ### 方向相同
                cond1 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnWI_orien_1")
                cond2 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnWI_orien_2")
                cond3 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnWI_orien_3")
                cond4 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnWI_orien_4")
                cond5 = model.BoolVar(f"{objects[obj['index']]['name']}_SetOnWI_orien_5")

                model.Add(obj['choose_baseline'][k+1] >= False - (1 - cond1) * 1e6) # 不是在WI的baseline上
                model.Add(obj['choose_baseline'][k+1] <= False + (1 - cond1) * 1e6) # 不是在WI的baseline上
                # 是的話 靠的方向要一樣
                model.Add(obj['orien_id'][0] + obj_set[k]['orien_id'][0] >= 2 - (1 - cond2) * 1e6)
                model.Add(obj['orien_id'][1] + obj_set[k]['orien_id'][1] >= 2 - (1 - cond3) * 1e6)
                model.Add(obj['orien_id'][2] + obj_set[k]['orien_id'][2] >= 2 - (1 - cond4) * 1e6)
                model.Add(obj['orien_id'][3] + obj_set[k]['orien_id'][3] >= 2 - (1 - cond5) * 1e6)
                model.Add(obj['orien_id'][0] + obj_set[k]['orien_id'][0] <= 2 + (1 - cond2) * 1e6)
                model.Add(obj['orien_id'][1] + obj_set[k]['orien_id'][1] <= 2 + (1 - cond3) * 1e6)
                model.Add(obj['orien_id'][2] + obj_set[k]['orien_id'][2] <= 2 + (1 - cond4) * 1e6)
                model.Add(obj['orien_id'][3] + obj_set[k]['orien_id'][3] <= 2 + (1 - cond5) * 1e6)

                model.Add(cond1 + cond2 + cond3 + cond4 + cond5 >= 1)
            
            ###########################################################################
            
            ##### 確保兩物件間的距離為正            
            cond1 = model.BoolVar(f"{objects[obj['index']]['name']}_dist_x1")
            cond2 = model.BoolVar(f"{objects[obj['index']]['name']}_dist_x2")
            
            model.Add(obj['distance'][0] >= obj['center_2'][0] - counter_set['center_2'][0] - (1 - cond1) * 1e6 - 0.005)
            model.Add(obj['distance'][0] <= obj['center_2'][0] - counter_set['center_2'][0] + (1 - cond1) * 1e6 + 0.005)
            model.Add(obj['distance'][0] >= counter_set['center_2'][0] - obj['center_2'][0] - (1 - cond2) * 1e6 - 0.005)            
            model.Add(obj['distance'][0] <= counter_set['center_2'][0] - obj['center_2'][0] + (1 - cond2) * 1e6 + 0.005)
            
            model.Add(cond1 + cond2 >= 1)
            
            cond1 = model.BoolVar(f"{objects[obj['index']]['name']}_dist_y1")
            cond2 = model.BoolVar(f"{objects[obj['index']]['name']}_dist_y2")
            
            model.Add(obj['distance'][1] >= obj['center_2'][1] - counter_set['center_2'][1] - (1 - cond1) * 1e6 - 0.005)
            model.Add(obj['distance'][1] <= obj['center_2'][1] - counter_set['center_2'][1] + (1 - cond1) * 1e6 + 0.005)
            model.Add(obj['distance'][1] >= counter_set['center_2'][1] - obj['center_2'][1] - (1 - cond2) * 1e6 - 0.005)            
            model.Add(obj['distance'][1] <= counter_set['center_2'][1] - obj['center_2'][1] + (1 - cond2) * 1e6 + 0.005)
            
            model.Add(cond1 + cond2 >= 1)
            
            ###########################################################################
            
            #### baseline的交界點外不能放置 (一般object對於WI/RI)
            
            for k in range(num_baseline-1): 
                ### counter靠在東邊(right靠牆) 所有物件的right<= counter['x']
                cond1 = model.BoolVar(f"{objects[obj['index']]['name']}_{k}")
                cond2 = model.BoolVar(f"{objects[obj['index']]['name']}_{k}")
                cond3 = model.BoolVar(f"{objects[obj['index']]['name']}_{k}")
                cond4 = model.BoolVar(f"{objects[obj['index']]['name']}_{k}")
                cond5 = model.BoolVar(f"{objects[obj['index']]['name']}_{k}")
                cond6 = model.BoolVar(f"{objects[obj['index']]['name']}_{k}")

                ### baseline 靠右(東)
                model.Add(obj_set[k]['orien_id'][0] >= 1 - (1 - cond1) * 1e6)  ### if baseline['orien_id'][0] = 1
                model.Add(obj_set[k]['orien_id'][0] <= 1 + (1 - cond1) * 1e6)
                model.Add(obj['right'] - (1 - obj['orien_id'][2] - obj['orien_id'][3]) * 1e6 <= obj_set[k]['x'] + (1 - cond1) * 1e6)
                model.Add(obj['top'] - (1 - obj['orien_id'][2]) * 1e6 <= obj_set[k]['y'] + (1 - cond1) * 1e6)  ### if obj['orien_id'][2] = 1
                model.Add(obj['y'] + (1 - obj['orien_id'][3]) * 1e6 >= obj_set[k]['top'] - (1 - cond1) * 1e6)  ### if obj['orien_id'][3] = 1
                
                ### baseline 靠左(西)
                model.Add(obj_set[k]['orien_id'][1] >= 1 - (1 - cond2) * 1e6)  ### if baseline['orien_id'][1] = 1
                model.Add(obj_set[k]['orien_id'][1] <= 1 + (1 - cond2) * 1e6)
                model.Add(obj['x'] + (1 - obj['orien_id'][2] - obj['orien_id'][3]) * 1e6 >= obj_set[k]['right'] - (1 - cond2) * 1e6)
                model.Add(obj['top'] - (1 - obj['orien_id'][2]) * 1e6 <= obj_set[k]['y'] + (1 - cond2) * 1e6)  ### if obj['orien_id'][2] = 1
                model.Add(obj['y'] + (1 - obj['orien_id'][3]) * 1e6 >= obj_set[k]['top'] - (1 - cond2) * 1e6)  ### if obj['orien_id'][3] = 1
                
                ### baseline 靠下(南)
                model.Add(obj_set[k]['orien_id'][2] >= 1 - (1 - cond3) * 1e6)  ### if baseline['orien_id'][2] = 1
                model.Add(obj_set[k]['orien_id'][2] <= 1 + (1 - cond3) * 1e6)
                model.Add(obj['y'] + (1 - obj['orien_id'][0] - obj['orien_id'][1]) * 1e6 >= obj_set[k]['top'] - (1 - cond3) * 1e6)
                model.Add(obj['x'] + (1 - obj['orien_id'][0]) * 1e6 >= obj_set[k]['right'] - (1 - cond3) * 1e6)  ### if obj['orien_id'][0] = 1
                model.Add(obj['right'] - (1 - obj['orien_id'][1]) * 1e6 <= obj_set[k]['x'] + (1 - cond3) * 1e6)  ### if obj['orien_id'][1] = 1
                
                ### baseline 靠上(北)
                model.Add(obj_set[k]['orien_id'][3] >= 1 - (1 - cond4) * 1e6)  ### if baseline['orien_id'][2] = 1
                model.Add(obj_set[k]['orien_id'][3] <= 1 + (1 - cond4) * 1e6)
                model.Add(obj['top'] - (1 - obj['orien_id'][0] - obj['orien_id'][1]) * 1e6 <= obj_set[k]['y'] + (1 - cond4) * 1e6)
                model.Add(obj['x'] + (1 - obj['orien_id'][0]) * 1e6 >= obj_set[k]['right'] - (1 - cond4) * 1e6)  ### if obj['orien_id'][0] = 1
                model.Add(obj['right'] - (1 - obj['orien_id'][1]) * 1e6 <= obj_set[k]['x'] + (1 - cond4) * 1e6)  ### if obj['orien_id'][1] = 1
                
                ### 同一個方向 或 在對面 就不用考慮
                model.Add(obj['orien_id'][0] + obj['orien_id'][1] + obj_set[k]['orien_id'][0] + obj_set[k]['orien_id'][1] >= 2 - (1 - cond5) * 1e6)
                model.Add(obj['orien_id'][0] + obj['orien_id'][1] + obj_set[k]['orien_id'][0] + obj_set[k]['orien_id'][1] <= 2 + (1 - cond5) * 1e6)
                model.Add(obj['orien_id'][2] + obj['orien_id'][3] + obj_set[k]['orien_id'][2] + obj_set[k]['orien_id'][3] >= 2 - (1 - cond6) * 1e6)
                model.Add(obj['orien_id'][2] + obj['orien_id'][3] + obj_set[k]['orien_id'][2] + obj_set[k]['orien_id'][3] <= 2 + (1 - cond6) * 1e6)

                model.Add(cond1 + cond2 + cond3 + cond4 + cond5 + cond6 >= 1)

        ##### 所有物件對於counter_baseline的交界點外不能放置
        cond1 = model.BoolVar(f"{objects[obj['index']]['name']}_bound1_counter")
        cond2 = model.BoolVar(f"{objects[obj['index']]['name']}_bound2_counter")
        cond3 = model.BoolVar(f"{objects[obj['index']]['name']}_bound3_counter")
        cond4 = model.BoolVar(f"{objects[obj['index']]['name']}_bound4_counter")
        cond5 = model.BoolVar(f"{objects[obj['index']]['name']}_bound5_counter")
        cond6 = model.BoolVar(f"{objects[obj['index']]['name']}_bound6_counter")

        ### counter 靠右(東)
        model.Add(counter_set['orien_id'][0] >= 1 - (1 - cond1) * 1e6)  ### if counter['orien_id'][0] = 1
        model.Add(counter_set['orien_id'][0] <= 1 + (1 - cond1) * 1e6)
        model.Add(obj['right'] - (1 - obj['orien_id'][2] - obj['orien_id'][3]) * 1e6 <= counter_set['x'] + (1 - cond1) * 1e6)
        model.Add(obj['top'] - (1 - obj['orien_id'][2]) * 1e6 <= counter_set['y'] + (1 - cond1) * 1e6)  ### if obj['orien_id'][2] = 1
        model.Add(obj['y'] + (1 - obj['orien_id'][3]) * 1e6 >= counter_set['top'] - (1 - cond1) * 1e6)  ### if obj['orien_id'][3] = 1
        
        ### counter 靠左(西)
        model.Add(counter_set['orien_id'][1] >= 1 - (1 - cond2) * 1e6)  ### if counter['orien_id'][1] = 1
        model.Add(counter_set['orien_id'][1] <= 1 + (1 - cond2) * 1e6)
        model.Add(obj['x'] + (1 - obj['orien_id'][2] - obj['orien_id'][3]) * 1e6 >= counter_set['right'] - (1 - cond2) * 1e6)
        model.Add(obj['top'] - (1 - obj['orien_id'][2]) * 1e6 <= counter_set['y'] + (1 - cond2) * 1e6)  ### if obj['orien_id'][2] = 1
        model.Add(obj['y'] + (1 - obj['orien_id'][3]) * 1e6 >= counter_set['top'] - (1 - cond2) * 1e6)  ### if obj['orien_id'][3] = 1
        
        ### counter 靠下(南)
        model.Add(counter_set['orien_id'][2] >= 1 - (1 - cond3) * 1e6)  ### if counter['orien_id'][2] = 1
        model.Add(counter_set['orien_id'][2] <= 1 + (1 - cond3) * 1e6)
        model.Add(obj['y'] + (1 - obj['orien_id'][0] - obj['orien_id'][1]) * 1e6 >= counter_set['top'] - (1 - cond3) * 1e6)
        model.Add(obj['x'] + (1 - obj['orien_id'][0]) * 1e6 >= counter_set['right'] - (1 - cond3) * 1e6)  ### if obj['orien_id'][0] = 1
        model.Add(obj['right'] - (1 - obj['orien_id'][1]) * 1e6 <= counter_set['x'] + (1 - cond3) * 1e6)  ### if obj['orien_id'][1] = 1
        
        ### counter 靠上(北)
        model.Add(counter_set['orien_id'][3] >= 1 - (1 - cond4) * 1e6)  ### if counter['orien_id'][2] = 1
        model.Add(counter_set['orien_id'][3] <= 1 + (1 - cond4) * 1e6)
        model.Add(obj['top'] - (1 - obj['orien_id'][0] - obj['orien_id'][1]) * 1e6 <= counter_set['y'] + (1 - cond4) * 1e6)
        model.Add(obj['x'] + (1 - obj['orien_id'][0]) * 1e6 >= counter_set['right'] - (1 - cond4) * 1e6)  ### if obj['orien_id'][0] = 1
        model.Add(obj['right'] - (1 - obj['orien_id'][1]) * 1e6 <= counter_set['x'] + (1 - cond4) * 1e6)  ### if obj['orien_id'][1] = 1
        
        ### 同一個方向 或 在對面 就不用考慮
        model.Add(obj['orien_id'][0] + obj['orien_id'][1] + counter_set['orien_id'][0] + counter_set['orien_id'][1] >= 2 - (1 - cond5) * 1e6)
        model.Add(obj['orien_id'][0] + obj['orien_id'][1] + counter_set['orien_id'][0] + counter_set['orien_id'][1] <= 2 + (1 - cond5) * 1e6)
        model.Add(obj['orien_id'][2] + obj['orien_id'][3] + counter_set['orien_id'][2] + counter_set['orien_id'][3] >= 2 - (1 - cond6) * 1e6)
        model.Add(obj['orien_id'][2] + obj['orien_id'][3] + counter_set['orien_id'][2] + counter_set['orien_id'][3] <= 2 + (1 - cond6) * 1e6)

        model.Add(cond1 + cond2 + cond3 + cond4 + cond5 + cond6 >= 1)

    ## 物件間的放置限制
    for i in range(len(obj_set)):
        ### 物件+走道不可以和其他物件重疊
        for j in range(len(obj_set)):
            if(i != j):
                cond1 = model.BoolVar(f'intersect1_obj_{i}_{j}')
                cond2 = model.BoolVar(f'intersect2_obj_{i}_{j}')
                cond3 = model.BoolVar(f'intersect3_obj_{i}_{j}')
                cond4 = model.BoolVar(f'intersect4_obj_{i}_{j}')

                model.Add(obj_set[i]['right'] + obj_set[i]['aisle'] * obj_set[i]['orien_id'][1] <= obj_set[j]['x'] + (1 - cond1) * 1e6) # 右1 <= 左2
                model.Add(obj_set[i]['top'] + obj_set[i]['aisle'] * obj_set[i]['orien_id'][2] <= obj_set[j]['y'] + (1 - cond2) * 1e6) # 上1 <= 下2
                model.Add(obj_set[i]['x'] - obj_set[i]['aisle'] * obj_set[i]['orien_id'][0] >= obj_set[j]['right'] - (1 - cond3) * 1e6) # 左1 >= 右2
                model.Add(obj_set[i]['y'] - obj_set[i]['aisle'] * obj_set[i]['orien_id'][3] >= obj_set[j]['top'] - (1 - cond4) * 1e6) # 下1 >= 上2

                model.Add(cond1 + cond2 + cond3 + cond4 >= 1)

        ### 不可以超過可行解區域    
        for cell in unusable_gridcell:
            
            if (cell['type'] == 'aisle'): ### 物件本身不可以放在走道上
                cond1 = model.BoolVar(f'intersect1_empty_{i}_e{j}')
                cond2 = model.BoolVar(f'intersect2_empty_{i}_e{j}')
                cond3 = model.BoolVar(f'intersect3_empty_{i}_e{j}')
                cond4 = model.BoolVar(f'intersect4_empty_{i}_e{j}')

                model.Add(obj_set[i]['right'] <= cell['x'] + (1 - cond1) * 1e6) # 右1 <= 左2
                model.Add(obj_set[i]['top'] <= cell['y'] + (1 - cond2) * 1e6) # 上1 <= 下2
                model.Add(obj_set[i]['x'] >= cell['x'] + cell['w'] - (1 - cond3) * 1e6) # 左1 >= 右2
                model.Add(obj_set[i]['y'] >= cell['y'] + cell['h'] - (1 - cond4) * 1e6) # 下1 >= 上2

                model.Add(cond1 + cond2 + cond3 + cond4 >= 1)
            
            else: ### 物件+走道
                ### 物件+走道不可以壓到其他已經放置的物件
                cond1 = model.BoolVar(f'intersect1_empty_{i}_e{j}')
                cond2 = model.BoolVar(f'intersect2_empty_{i}_e{j}')
                cond3 = model.BoolVar(f'intersect3_empty_{i}_e{j}')
                cond4 = model.BoolVar(f'intersect4_empty_{i}_e{j}')

                model.Add(obj_set[i]['right'] + obj_set[i]['aisle'] * obj_set[i]['orien_id'][1] <= cell['x'] + (1 - cond1) * 1e6) # 右1 <= 左2
                model.Add(obj_set[i]['top'] + obj_set[i]['aisle'] * obj_set[i]['orien_id'][2] <= cell['y'] + (1 - cond2) * 1e6) # 上1 <= 下2
                model.Add(obj_set[i]['x'] - obj_set[i]['aisle'] * obj_set[i]['orien_id'][0] >= cell['x'] + cell['w'] - (1 - cond3) * 1e6) # 左1 >= 右2
                model.Add(obj_set[i]['y'] - obj_set[i]['aisle'] * obj_set[i]['orien_id'][3] >= cell['y'] + cell['h'] - (1 - cond4) * 1e6) # 下1 >= 上2

                model.Add(cond1 + cond2 + cond3 + cond4 >= 1)
                
                ### 物件+走道不可以超出可行解區域
                model.Add(obj_set[i]['right'] + obj_set[i]['aisle'] * obj_set[i]['orien_id'][1] <= max_x) # 右1 <= 左2
                model.Add(obj_set[i]['top'] + obj_set[i]['aisle'] * obj_set[i]['orien_id'][2] <= max_y) # 上1 <= 下2
                model.Add(obj_set[i]['x'] - obj_set[i]['aisle'] * obj_set[i]['orien_id'][0] >= min_x) # 左1 >= 右2
                model.Add(obj_set[i]['y'] - obj_set[i]['aisle'] * obj_set[i]['orien_id'][3] >= min_y) # 下1 >= 上2

    ### 在物件和baseline object中間要預留一小段走道
    reserve_aisle = 100
    for i in range(num_baseline-1,len(obj_set)):
        ### 和counter間
        cond1 = model.BoolVar(f'reverse1_aisle_obj_{i}_counter')
        cond2 = model.BoolVar(f'reverse2_aisle_obj_{i}_counter')
        cond3 = model.BoolVar(f'reverse3_aisle_obj_{i}_counter')
        cond4 = model.BoolVar(f'reverse4_aisle_obj_{i}_counter')
        cond5 = model.BoolVar(f'reverse5_aisle_obj_{i}_counter')

        ### 如果不是放在baseline_counter就不需要考慮
        model.Add(obj_set[i]['choose_baseline'][0] >= False - (1 - cond1) * 1e6) ### 如果不是放在baseline_counter就不需要考慮
        model.Add(obj_set[i]['choose_baseline'][0] <= False + (1 - cond1) * 1e6) ### 如果不是放在baseline_counter就不需要考慮
        
        model.Add(obj_set[i]['right'] + reserve_aisle + 10000 * (1 - obj_set[i]['orien_id'][2] - obj_set[i]['orien_id'][3] ) <= counter_set['x'] + (1 - cond2) * 1e6) # 右1 <= 左2
        model.Add(obj_set[i]['top'] + reserve_aisle + 10000 * (1 - obj_set[i]['orien_id'][0] - obj_set[i]['orien_id'][1] ) <= counter_set['y'] + (1 - cond3) * 1e6) # 上1 <= 下2
        model.Add(obj_set[i]['x'] - reserve_aisle - 10000 * (1 - obj_set[i]['orien_id'][2] - obj_set[i]['orien_id'][3] ) >= counter_set['right'] - (1 - cond4) * 1e6) # 左1 >= 右2
        model.Add(obj_set[i]['y'] - reserve_aisle - 10000 * (1 - obj_set[i]['orien_id'][0] - obj_set[i]['orien_id'][1] ) >= counter_set['top'] - (1 - cond5) * 1e6) # 下1 >= 上2

        model.Add(cond1 + cond2 + cond3 + cond4 + cond5 >= 1)

        # ### 和其他baseline_objects間
        for k in range(num_baseline-1):
            cond1 = model.BoolVar(f'reverse1_aisle_obj_{i}_{k}')
            cond2 = model.BoolVar(f'reverse2_aisle_obj_{i}_{k}')
            cond3 = model.BoolVar(f'reverse3_aisle_obj_{i}_{k}')
            cond4 = model.BoolVar(f'reverse4_aisle_obj_{i}_{k}')
            cond5 = model.BoolVar(f'reverse5_aisle_obj_{i}_{k}')

            ### 如果不是放在baseline_counter就不需要考慮
            model.Add(obj_set[i]['choose_baseline'][k+1] >= False - (1 - cond1) * 1e6) ### 如果不是放在baseline_counter就不需要考慮
            model.Add(obj_set[i]['choose_baseline'][k+1] <= False + (1 - cond1) * 1e6) ### 如果不是放在baseline_counter就不需要考慮
            
            model.Add(obj_set[i]['right'] + reserve_aisle + 10000 * (1 - obj_set[i]['orien_id'][2] - obj_set[i]['orien_id'][3] ) <= obj_set[k]['x'] + (1 - cond2) * 1e6) # 右1 <= 左2
            model.Add(obj_set[i]['top'] + reserve_aisle + 10000 * (1 - obj_set[i]['orien_id'][0] - obj_set[i]['orien_id'][1] ) <= obj_set[k]['y'] + (1 - cond3) * 1e6) # 上1 <= 下2
            model.Add(obj_set[i]['x'] - reserve_aisle - 10000 * (1 - obj_set[i]['orien_id'][2] - obj_set[i]['orien_id'][3] ) >= obj_set[k]['right'] - (1 - cond4) * 1e6) # 左1 >= 右2
            model.Add(obj_set[i]['y'] - reserve_aisle - 10000 * (1 - obj_set[i]['orien_id'][0] - obj_set[i]['orien_id'][1] ) >= obj_set[k]['top'] - (1 - cond5) * 1e6) # 下1 >= 上2

            model.Add(cond1 + cond2 + cond3 + cond4 + cond5 >= 1)

    #########################################################################################

    ### Objective Function
    ### 讓OC/單溫/雙溫最靠近counter
    ### 與counter中點直角座標距離最短
    total_distance = 0.0
    for obj in obj_set:
        if(obj['set_wall']==False):
            total_distance += obj['distance'][0]
            total_distance += obj['distance'][1]
    
    model.Minimize(total_distance)

    ### 紀錄求解時間
    start_time = time.time()

    ### solution
    status = model.Solve()
    # solver = cp_model.CpSolver()
    # status = solver.Solve(model)

    end_time = time.time()
    solve_time = end_time - start_time
    print("solve_time = ",solve_time)

    baseline_result = []
    baseline_result_orien_id = []
    ### record solution
    if status == pywraplp.Solver.OPTIMAL:
    # if status == cp_model.OPTIMAL:
        for cell in obj_set:
            ### 物件 name, x, y, w, h
            name = cell['name']
            set_x, set_y = round(cell['x'].solution_value(),4), round(cell['y'].solution_value(),4)
            w = round(cell['right'].solution_value() - cell['x'].solution_value(),4)
            h = round(cell['top'].solution_value() - cell['y'].solution_value(),4)
            # baseline_result.append({'name':name, 'x':set_x, 'y':set_y, 'w':w, 'h':h, 'type':'objects'})
            
            ### 物件 orien_id
            orien_id = [cell['orien_id'][0].solution_value(),cell['orien_id'][1].solution_value(),
                        cell['orien_id'][2].solution_value(),cell['orien_id'][3].solution_value() ]
            if orien_id[0] == 1:
                orientation = 'east'
            elif orien_id[1] == 1:
                orientation = 'west'
            elif orien_id[2] == 1:
                orientation = 'south'
            else:
                orientation = 'north'
                
            tmp_cell_result = {'name': name, 'x': set_x, 'y': set_y, 'w': w, 'h': h, 'type': 'objects','orientation':orientation}
            
            if(cell['set_wall']==False): ### OC/單溫/雙溫
                print(cell['name'],cell['center_2'][0].solution_value(),cell['center_2'][1].solution_value(),"distance",cell['distance'][0].solution_value(),cell['distance'][1].solution_value())
                # print(cell['x'].solution_value(), cell['y'].solution_value(),cell['right'].solution_value(),cell['top'].solution_value())
                choose_baseline = [int(cell['choose_baseline'][0].solution_value())]
                for i in range(len(objects_for_set_baseline)):
                    choose_baseline.append(int(cell['choose_baseline'][i+1].solution_value()))
                tmp_cell_result['choose_baseline'] = choose_baseline
                
                # print("counter",counter_set['center_2'][0],counter_set['center_2'][1])
                # print("distance",counter_set['center_2'][0] - cell['center_2'][0].solution_value(),counter_set['center_2'][1]- cell['center_2'][1].solution_value())
            baseline_result.append(tmp_cell_result)

    else:
        print('未找到最佳解')

    return baseline_result, baseline_result_orien_id

def choose_feasible_wall(objects,wall,set_on_counter_wall,counter_orientation,set_on_gate_wall,gate_orientation):
    ### 挑選合適的牆面
    feasible_wall = []
    min_object_width = min(obj['w'] for obj in objects if obj['name'] in ['WI', 'RI'])
    
    for cell in wall:
        if(cell['range'][1]-cell['range'][0] < min_object_width):
            continue
        if(set_on_counter_wall == False and cell['orientation']==counter_orientation):
            continue
        if(set_on_gate_wall == False and cell['orientation']==gate_orientation):
            continue
        feasible_wall.append(cell)
    
    # print(feasible_wall)
    return feasible_wall

def get_part_shape(object ,baseline ,min_x, max_x, min_y, max_y):
    if(baseline['orientation']=='east'):
        if(object['y'] >= baseline['y'] + baseline['h']): # 在右上
            tmp_baseline_combination = {'x':baseline['x'],'y':baseline['y']+baseline['h'],
                                        'w':max_x-baseline['x'],'h':max_y-(baseline['y']+baseline['h'])}
        else: # 在右下
            tmp_baseline_combination = {'x':baseline['x'],'y':min_y,
                                        'w':max_x-baseline['x'],'h':baseline['y']-min_y}
    elif(baseline['orientation']=='west'):
        if(object['y'] >= baseline['y'] + baseline['h']): # 在左上
            tmp_baseline_combination = {'x':min_x,'y':(baseline['y']+baseline['h']),
                                        'w':(baseline['x']+baseline['w'])-min_x,'h':max_y-(baseline['y']+baseline['h'])}
        else: # 在左下
            tmp_baseline_combination = {'x':min_x,'y':min_y,
                                        'w':(baseline['x']+baseline['w'])-min_x,'h':baseline['y']-min_y}
    elif(baseline['orientation']=='south'):
        if(object['x'] >= baseline['x'] + baseline['w']): # 在右下
            tmp_baseline_combination = {'x':(baseline['x']+baseline['w']),'y':min_y,
                                        'w':max_x-(baseline['x']+baseline['w']),'h':(baseline['y']+baseline['h'])-min_y}
        else: # 在左下
            tmp_baseline_combination = {'x':min_x,'y':min_y,
                                        'w':baseline['x']-min_x,'h':(baseline['y']+baseline['h'])-min_y}
    else: # baseline['orientation']=='north'
        if(object['x'] >= baseline['x'] + baseline['w']): # 在右上
            tmp_baseline_combination = {'x':baseline['x']+baseline['w'],'y':baseline['y'],
                                        'w':max_x-(baseline['x']+baseline['w']),'h':max_y-baseline['y']}
        else: # 在左上                
            tmp_baseline_combination = {'x':min_x,'y':baseline['y'],
                                        'w':baseline['x']-min_x,'h':max_y-baseline['y']}
    return(tmp_baseline_combination)

def set_back_work_area(baseline_result,objects_for_set_baseline,counter_set,unusable_gridcell,min_x, max_x, min_y, max_y):
    baseline_set = [counter_set]
    for i in range(len(objects_for_set_baseline)):
        baseline_set.append(baseline_result[i])
    baseline_combination = []
    for i in range(len(objects_for_set_baseline),len(baseline_result)):
        baseline_object_id = baseline_result[i]['choose_baseline'].index(1)
        tmp_baseline_combination = get_part_shape(baseline_result[i],baseline_set[baseline_object_id],min_x,max_x,min_y,max_y)
        ### 檢查是不是有重複
        check_combination = False
        for cell in baseline_combination:
            if(tmp_baseline_combination == cell):
                check_combination = True
        if(check_combination == False):
            baseline_combination.append(tmp_baseline_combination)
    
    ### 確保有counter畫出的baseline
    for i in range(len(objects_for_set_baseline),len(baseline_result)):
        tmp_baseline_combination = get_part_shape(baseline_result[i],baseline_set[0],min_x,max_x,min_y,max_y)
        ### 檢查是不是有重複
        check_combination = False
        for cell in baseline_combination:
            if(tmp_baseline_combination == cell):
                check_combination = True
        if(check_combination == False):
            baseline_combination.append(tmp_baseline_combination)

    return(baseline_combination)

def baseline_placements(obj_params, unusable_gridcell, min_x, max_x, min_y, max_y, wall, door, counter_result, counter_placement, unusable_gridcell1, available_segments, DOOR_placement):
    unusable_gridcell, counter_set = transform_counter(counter_placement, unusable_gridcell1)

    ### 設置baseline的物件
    baseline_object = ['WI','RI']
    set_on_baseline_object = ['OC','S_T','D_T']
    
    objects = [
        {'name': 'WI', 'w': 365, 'h': 270, 'num':1, 'aisle': 120, 'have_pillar': True, 'set_type':'baseline_objects'}, #WI冷藏區
        {'name': 'RI', 'w': 310, 'h': 225, 'num':1,'aisle': 120, 'have_pillar': False, 'set_type':'baseline_objects'},  #RI冷凍區
        {'name': 'OC', 'w': 90, 'h': 66, 'num':2,'aisle': 120, 'have_pillar': False, 'set_type':'set_objects'},  #OC
        {'name': 'S_T', 'w': 90, 'h': 66, 'num':2,'aisle': 120, 'have_pillar': False, 'set_type':'set_objects'},  #單溫櫃/生鮮區
        {'name': 'D_T', 'w': 90, 'h': 66, 'num':2,'aisle': 120, 'have_pillar': False, 'set_type':'set_objects'}  #雙溫櫃/開放區
    ]
    
    ### 設置用來畫baseline的物件、需要被放置在baseline的物件
    objects_for_set_baseline = ['WI','RI'] # 除了counter以外的
    objects_set_on_baseline = ['OC','S_T','D_T']
    
    # ## 傳這個很慢
    # objects = []
    # for key, value in obj_params.items():
    #     tmp_obj = {}
    #     if(value['group']==0.1):
    #         tmp_obj['set_type'] = 'baseline_objects'
    #     elif(value['group'] ==0.2):
    #         tmp_obj['set_type'] = 'set_objects'
    #     else: ### 都不是表示不用放置
    #         continue
    #     tmp_obj['name'] = value['name']
    #     tmp_obj['w'], tmp_obj['h'] = max(value['w_h']), min(value['w_h'])
    #     tmp_obj['num'] = value['num']
    #     tmp_obj['aisle'] = value['aisle']
    #     objects.append(tmp_obj)
        
    ### 挑選WI/RI可放置的合適牆面
    set_on_counter_wall = False
    set_on_gate_wall = False
    feasible_wall = choose_feasible_wall(objects,wall,set_on_counter_wall,counter_placement,set_on_gate_wall,DOOR_placement)
    baseline_result, baseline_result_orien_id = optimization(objects, objects_for_set_baseline, counter_set, feasible_wall, unusable_gridcell, min_x, max_x, min_y, max_y)

    ##### 更新unusable_gridcell
    for index, cell in enumerate(baseline_result):
        ##### 加入已經占用的空間紀錄
        unusable_gridcell.append(cell)
        ##### 預留走道
        aisle = next(objects[id]['aisle'] for id, obj in enumerate(objects) if obj.get('name') == cell['name'])
        
        if(cell['orientation'] == 'east'):
            unusable_gridcell.append({'type':'aisle', 'x':cell['x']-aisle, 'y':cell['y'], 'w':aisle, 'h':cell['h']})
        elif(cell['orientation'] == 'west'):
            unusable_gridcell.append({'type':'aisle', 'x':cell['x']+cell['w'], 'y':cell['y'], 'w':aisle, 'h':cell['h']})
        elif(cell['orientation'] == 'south'):
            unusable_gridcell.append({'type':'aisle', 'x':cell['x'], 'y':cell['y']+cell['h'], 'w':cell['w'], 'h':aisle})
        else: # cell['orientation'] == 'north'
            unusable_gridcell.append({'type':'aisle', 'x':cell['x'], 'y':cell['y']-aisle, 'w':cell['w'], 'h':aisle})
    
    ### 圍出的後場作業區
    back_work_area = set_back_work_area(baseline_result,objects_for_set_baseline,counter_set,unusable_gridcell,min_x, max_x, min_y, max_y)
    ### 加入結果
    for cell in back_work_area:
        cell['type'] = 'back_work_area'
        cell['name'] = 'OC_back_work_area'
        unusable_gridcell.append(cell)
    
    ##### 轉換unusable_gridcell --- list -> dictionary
    renew_unusable_gridcell = {}
    for index, cell in enumerate(unusable_gridcell):
        renew_unusable_gridcell[index] = cell
    baseline_result_dict = {i: item for i, item in enumerate(baseline_result)}
    print(baseline_object)
    return baseline_result_dict, renew_unusable_gridcell

if __name__ == '__main__':
    ### test dxf
    # doc ='/home/server4090-3/Nancy17/layout/inputdxf/revise.dxf'
    # doc = '/home/server4090-3/Nancy17/layout/inputdxf/九如東寧_可.dxf'
    # doc = '/home/server4090-3/Nancy17/layout/inputdxf/岡山竹東_可.dxf'
    # doc = '/home/server4090-3/Nancy17/layout/inputdxf/潭子新大茂_可.dxf' ### dxf有問題
    # doc = '/home/server4090-3/Nancy17/layout/inputdxf/六甲水林.dxf'
    doc = '/home/server4090-3/Nancy17/layout/inputdxf/竹南旺大埔.dxf'
    
    unusable_gridcell,unusable_gridcell_dict, min_x, max_x, min_y, max_y, poly_feasible, wall, door, frontdoor = get_feasible_area.feasible_area(doc)
    # unusable_gridcell, min_x, max_x, min_y, max_y, poly_feasible, wall, door = get_feasible_area.get_feasible_area(doc)

    ### 設置大門方位
    # Space for door entry
    DOOR_PLACEMENT = frontdoor  # 大門位置
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

    SPACE_WIDTH,SPACE_HEIGHT= max_x-min_x+1, max_y-min_y+1
    AISLE_SPACE = 100
    COUNTER_SPACING = 110
    OPENDOOR_SPACING = 110
    LINEUP_SPACING = 160
    
    #Define the parameters and variables
    obj_params = {
        0: {'group':2,'w_h': [SPACE_WIDTH,SPACE_HEIGHT], 'fixed_wall': 'none', 'name':'貨架區', },
        1: {'group':0,'w_h': [465,66], 'fixed_wall': 'none', 'name':'前櫃檯'},
        2: {'group':0,'w_h': [598,66], 'fixed_wall': 'any', 'name':'後櫃檯'},
        3: {'group':0.1,'w_h': [365,270], 'fixed_wall': 'any', 'name':'WI', 'num':1, 'aisle': 120}, 
        4: {'group':0.2,'w_h': [90,66], 'fixed_wall': 'none', 'name':'D_T', 'num':2, 'aisle': 120},
        5: {'group':0.2,'w_h': [90,66], 'fixed_wall': 'none', 'name':'S_T', 'num':2, 'aisle': 120},
        6: {'group':0.2,'w_h': [90,66], 'fixed_wall': 'none', 'name':'OC', 'num':2, 'aisle': 120},
        7: {'group':0.1,'w_h': [310,225], 'fixed_wall': 'any', 'name':'RI', 'num':1, 'aisle': 120},
        8: {'group':1,'w_h': [95,59], 'fixed_wall': 'any', 'name':'EC'},
        9: {'group':1,'w_h': [190,90], 'fixed_wall': 'any', 'name':'子母櫃'},
        10: {'group':1,'w_h': [100,85], 'fixed_wall': 'any', 'name':'ATM'},
        11: {'group':1,'w_h': [83,64], 'fixed_wall': 'any', 'name':'影印'},
        12: {'group':1,'w_h': [80,55], 'fixed_wall': 'any', 'name':'KIOSK'}
    }
    
    result_0, counter_placement, unusable_gridcell0, available_segments = opt_group0.counter_placements(unusable_gridcell_dict, poly_feasible, obj_params, COUNTER_SPACING, LINEUP_SPACING, DOOR_PLACEMENT, DOOR_ENTRY, min_x, max_x, min_y, max_y)
    # counter_result, counter_placement, unusable_gridcell_1, available_segments = opt_group0.counter_placements(poly_feasible, obj_params, COUNTER_SPACING, LINEUP_SPACING, DOOR_PLACEMENT, DOOR_ENTRY, min_x, max_x, min_y, max_y)
    
    ##### 放置WI、RI、OC/單溫/雙溫
    # baseline_result, unusable_gridcell = baseline_placements(obj_params, unusable_gridcell, min_x, max_x, min_y, max_y, wall, door, counter_result, counter_placement, unusable_gridcell_1, available_segments, DOOR_placement)
    result_0102, unusable_gridcell0102 = baseline_placements(obj_params, unusable_gridcell, min_x, max_x, min_y, max_y, wall, door, result_0, counter_placement, unusable_gridcell0, available_segments, DOOR_placement)
    
    # print("result")
    # for key, values in result_0102.items():
    #     print(values)
        
    ####################################################################################################
    
    ### 創建新圖
    fig, ax = plt.subplots()

    ### 放置物件區域
    ax.add_patch(plt.Rectangle((0, 0), max_x, max_y, edgecolor='black', facecolor='none'))

    ### 繪製 empty area、objects、aisle
    for key, cell in unusable_gridcell0102.items():
        x,y = cell['x'], cell['y']
        width, height =  cell['w'], cell['h']

        if(cell['type']=='empty_area'):
            ax.add_patch(plt.Rectangle((x,y), width, height, edgecolor='black', facecolor='black'))
        elif(cell['type']=='objects'):
            # print(cell)
            ax.add_patch(plt.Rectangle((x,y), width, height, edgecolor='red', facecolor='none'))
            ax.annotate(cell['name'], (x + width/2, y + height/2), color='black', weight='bold', fontsize=10,
                ha='center', va='center')
        elif(cell['type']=='aisle'):
            ax.add_patch(plt.Rectangle((x,y), width, height, edgecolor='grey', linestyle='--', facecolor='none'))
        elif(cell['type']=='taisle'):
            ax.add_patch(plt.Rectangle((x,y), width, height, edgecolor='green', linestyle='--', facecolor='none'))

    ### 設定x,y軸名稱、標題
    ax.set_title('Area with Feasible Area')
    ax.set_xlabel('Width')
    ax.set_ylabel('Height')

    ### 座標範圍
    ax.set_xlim(0, max_x)
    ax.set_ylim(0, max_y)

    ### 存檔
    plt.savefig('/home/server4090-3/Nancy17/layout/test_output/test0102_竹南.png', dpi=300, bbox_inches='tight')
    
    ### 顯示圖形
    plt.show()
