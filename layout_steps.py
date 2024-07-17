import gurobipy as gp
from gurobipy import GRB
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib
from tools import get_range
import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment
from tools import get_feasible_area
from tools import KPtest
from tools import coordinate_flipping as flip
from tools import get_feasible_area

DualReductions = 0

def layout_opt_group1(obj_params,COUNTER_SPACING, SPACE_WIDTH, SPACE_HEIGHT, OPENDOOR_SPACING, LINEUP_SPACING, unusable_gridcell):
    # Create a Gurobi model
    start_time = time.time()
    model = gp.Model("layout_generation_front desk")
    model.params.NonConvex = 2
    
    num_objects = len(obj_params)
    num_unusable_cells = len(unusable_gridcell)
    
    optgroup_1 = {}

    temp = 0
    for i in range(num_objects):
        if obj_params[i]['group']==1:
            optgroup_1.update({temp:obj_params[i]})
            temp+=1

    num_optgroup1 = len(optgroup_1)
    for i in range(num_optgroup1):
        if optgroup_1[i]['name']=='前櫃檯':
            f = i
        if optgroup_1[i]['name']=='後櫃檯':
            b = i
    
    p, q, s, t, orientation = {}, {}, {}, {}, {}
    x, y, w, h, select, T = {}, {}, {}, {}, {}, {}
    # Binary variables
    for i in range(num_optgroup1):
        for j in range(num_optgroup1):
            if i != j:
                p[i, j] = model.addVar(vtype=GRB.BINARY, name=f"p_{i}_{j}")
                q[i, j] = model.addVar(vtype=GRB.BINARY, name=f"q_{i}_{j}")
        for k in range(num_unusable_cells):
            s[i, k] = model.addVar(vtype=GRB.BINARY, name=f"s_{i}_{k}")
            t[i, k] = model.addVar(vtype=GRB.BINARY, name=f"t_{i}_{k}")
        orientation[i] = model.addVar(vtype=GRB.BINARY, name=f"orientation_{i}")

    # Dimension variables
    for i in range(num_optgroup1):
        x[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"x_{i}")
        y[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"y_{i}")
        w[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"w_{i}")
        h[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"h_{i}")

        for k in range(4):
            select[i,k] = model.addVar(vtype=GRB.BINARY, name=f"select_{i,k}")
    
        for j in range(num_optgroup1):
            T[i,j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"T_{i,j}")


    # Set objective
    #model.setObjective(gp.quicksum(w[i]*h[i] for i in range(num_optgroup1)), GRB.MINIMIZE)
    #model.setParam('TimeLimit', 1800)
    total_area = gp.quicksum(w[i] * h[i] for i in range(num_optgroup1))
    coor =gp.quicksum(x[i] + y[i] for i in range(num_optgroup1))
    model.setObjective((total_area), GRB.MINIMIZE)
    # Set constraints for general specifications
    # Connectivity constraint
    for i in range(num_optgroup1):
        if not optgroup_1[i]['connect']:
            pass
        else:
            for j in obj_params[i]['connect']:
                print(f'connect{j}')

                # Constraint that ensure that object i is to the left of or adjacent to object j when p[i, j] + q[i, j] = 0.
                model.addConstr(x[i] + w[i] >= x[j] - SPACE_WIDTH*(p[i,j] + q[i,j]), name="Connectivity Constraint 1")

                # Constraint that ensures that the bottom side of object i is at least as low as the top side of object j 
                # when 1 + p[i, j] - q[i, j] = 0, ensuring vertical adjacency or overlap.
                model.addConstr(y[i] + h[i] >= y[j] - SPACE_HEIGHT*(1 + p[i,j] - q[i,j]), name="Connectivity Constraint 2")
                
                # Constraint that ensures that the right side of object j is at least as far to the right as the left side of object i,
                # meaning object j can be to the right of, or overlapping, or adjacent to object i.
                model.addConstr(x[j] + w[j] >= x[i] - SPACE_WIDTH*(1 - p[i,j] + q[i,j]), name = "Connectivity Constraint 3")
                
                # Constraint that ensures that the bottom side of object j is at least as low as the top side of object i,
                model.addConstr(y[j] + h[j] >= y[i] - SPACE_HEIGHT*(2 - p[i,j] - q[i,j]), name = "Connectivity Constraint 4")
                
                model.addConstr(0.5*(w[i]+w[j]) >= T[i,j] + (y[j] - y[i]) - SPACE_WIDTH*(p[i,j] + q[i,j]), name="overlap constraint_18")
                model.addConstr(0.5*(h[i]+h[j]) >= T[i,j] + (x[j] - x[i]) - SPACE_HEIGHT*(2 - p[i,j] - q[i,j]), name="overlap constraint_19")
                model.addConstr(0.5*(w[i]+w[j]) >= T[i,j] + (y[i] - y[j]) - SPACE_WIDTH*(1 - p[i,j] + q[i,j]), name="overlap constraint_20")
                model.addConstr(0.5*(h[i]+h[j]) >= T[i,j] + (x[i] - x[j]) - SPACE_HEIGHT*(1 + p[i,j] - q[i,j]), name="overlap constraint_21")

    # Boundary constraints
    for i in range(num_optgroup1):
        model.addConstr(x[i] + w[i] <= SPACE_WIDTH, name="Boundary constraint for x")
        model.addConstr(y[i] + h[i] <= SPACE_HEIGHT, name="Boundary constraint for y")
    
    # Fixed border constraint
    for i in range(num_optgroup1):
        if not optgroup_1[i]['fixed_wall']:
            print(f'No fixed wall constraint for object {i}')
        elif optgroup_1[i]['fixed_wall']== 'any':
            # 選靠哪面牆
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(optgroup_1[i]['w_h'])-SPACE_WIDTH+1)*select[i,1]+(y[i]+1)*select[i,2]
                            +(y[i]+min(optgroup_1[i]['w_h'])-SPACE_HEIGHT+1)*select[i,3]==1, name='any constraint')
        elif optgroup_1[i]['fixed_wall'] == 'north':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(optgroup_1[i]['w_h'])-SPACE_WIDTH+1)*select[i,1]+(y[i]+1)*select[i,2]
                            +(y[i]+min(optgroup_1[i]['w_h'])-SPACE_HEIGHT+1)*select[i,3]==1, name='any constraint')
            model.addConstr(select[i,2]==1, name="North border constraint")
        elif optgroup_1[i]['fixed_wall']== 'south':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(optgroup_1[i]['w_h'])-SPACE_WIDTH+1)*select[i,1]+(y[i]+1)*select[i,2]
                            +(y[i]+min(optgroup_1[i]['w_h'])-SPACE_HEIGHT+1)*select[i,3]==1, name='any constraint')
            model.addConstr(select[i,3]==1, name="South border constraint")
        elif optgroup_1[i]['fixed_wall']== 'east':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(optgroup_1[i]['w_h'])-SPACE_WIDTH+1)*select[i,1]+(y[i]+1)*select[i,2]
                            +(y[i]+min(optgroup_1[i]['w_h'])-SPACE_HEIGHT+1)*select[i,3]==1, name='any constraint')
            model.addConstr(select[i,1]==1, name="East border constraint")
        elif optgroup_1[i]['fixed_wall']== 'west':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(optgroup_1[i]['w_h'])-SPACE_WIDTH+1)*select[i,1]+(y[i]+1)*select[i,2]
                            +(y[i]+min(optgroup_1[i]['w_h'])-SPACE_HEIGHT+1)*select[i,3]==1, name='any constraint')
            model.addConstr(select[i,0]==1, name="West border constraint")
            
    # Non-intersecting with aisle constraint
    for i in range(num_optgroup1):
        for j in range(num_optgroup1):
            if not optgroup_1[i]['connect'] and i != j:
                if [i, j] == [f,b] or [i,j]==[b,f]:
                    model.addConstr((orientation[i]==0)>>(x[i] + w[i] + COUNTER_SPACING <= x[j] + SPACE_WIDTH * (p[i,j] + q[i,j])), name="Non-intersecting Constraint 1")
                    model.addConstr((orientation[i]==1)>>(y[i] + h[i] + COUNTER_SPACING <= y[j] + SPACE_HEIGHT * (1 + p[i,j] - q[i,j])), name="Non-intersecting Constraint 2")
                    model.addConstr((orientation[i]==0)>>(x[j] + w[j] + COUNTER_SPACING <= x[i] + SPACE_WIDTH * (1 - p[i,j] + q[i,j])), name = "Non-intersecting Constraint 3")
                    model.addConstr((orientation[i]==1)>>(y[j] + h[j] + COUNTER_SPACING <= y[i] + SPACE_HEIGHT * (2 - p[i,j] - q[i,j])), name = "Non-intersecting Constraint 4")

                    model.addConstr((orientation[i]==0)>>(x[i] + w[i] + COUNTER_SPACING >= x[j] - SPACE_WIDTH * (p[i,j] + q[i,j])), name="Non-intersecting Constraint 1")
                    model.addConstr((orientation[i]==1)>>(y[i] + h[i] + COUNTER_SPACING >= y[j] - SPACE_HEIGHT * (1 + p[i,j] - q[i,j])), name="Non-intersecting Constraint 2")
                    model.addConstr((orientation[i]==0)>>(x[j] + w[j] + COUNTER_SPACING >= x[i] - SPACE_WIDTH * (1 - p[i,j] + q[i,j])), name = "Non-intersecting Constraint 3")
                    model.addConstr((orientation[i]==1)>>(y[j] + h[j] + COUNTER_SPACING >= y[i] - SPACE_HEIGHT * (2 - p[i,j] - q[i,j])), name = "Non-intersecting Constraint 4")
                else:
                    # non-intersecting constraints
                    # object i to the left of object j
                    model.addConstr(x[i] + w[i] + AISLE_SPACE <= x[j] + SPACE_WIDTH * (p[i,j] + q[i,j]), name="Non-intersecting Constraint 1")
                    
                    # object i above object j
                    model.addConstr(y[i] + h[i] + AISLE_SPACE <= y[j] + SPACE_HEIGHT * (1 + p[i,j] - q[i,j]), name="Non-intersecting Constraint 2")
                    
                    # object i to the right of object j
                    model.addConstr(x[j] + w[j] + AISLE_SPACE <= x[i] + SPACE_WIDTH * (1 - p[i,j] + q[i,j]), name = "Non-intersecting Constraint 3")
                    
                    # object i below object j
                    model.addConstr(y[j] + h[j] + AISLE_SPACE <= y[i] + SPACE_HEIGHT * (2 - p[i,j] - q[i,j]), name = "Non-intersecting Constraint 4")
            elif i!=j:
                model.addConstr(x[i] + w[i] <= x[j] + SPACE_WIDTH * (p[i,j] + q[i,j]), name="Non-intersecting Constraint 1")
                model.addConstr(y[i] + h[i] <= y[j] + SPACE_HEIGHT * (1 + p[i,j] - q[i,j]), name="Non-intersecting Constraint 2")
                model.addConstr(x[j] + w[j] <= x[i] + SPACE_WIDTH * (1 - p[i,j] + q[i,j]), name = "Non-intersecting Constraint 3")
                model.addConstr(y[j] + h[j] <= y[i] + SPACE_HEIGHT * (2 - p[i,j] - q[i,j]), name = "Non-intersecting Constraint 4")


    # Length constraint
    for i in range(num_optgroup1):
        model.addConstr(w[i]==[min(optgroup_1[i]['w_h']),max(optgroup_1[i]['w_h'])] , name="Length Constraint 1")
        model.addConstr(h[i] == [min(optgroup_1[i]['w_h']), max(optgroup_1[i]['w_h'])], name="Height Constraint 2")

    # Unusable grid cell constraint
    for i in range(num_optgroup1):
        for k in range(num_unusable_cells):
            model.addConstr(x[i] >= unusable_gridcell[k]['x']+ unusable_gridcell[k]['w'] + 1 - SPACE_WIDTH * (s[i,k] + t[i,k]), name="Unusable grid cell 1")
            model.addConstr(unusable_gridcell[k]['x'] >= x[i] + w[i] - SPACE_WIDTH * (1 + s[i,k] - t[i,k]), name="Unusable grid cell 2")
            model.addConstr(y[i] >= unusable_gridcell[k]['y'] + unusable_gridcell[k]['h'] + 1 - SPACE_HEIGHT * (1 - s[i,k] + t[i,k]), name = "Unusable grid cell 3")
            model.addConstr(unusable_gridcell[k]['y'] >= y[i] + h[i] - SPACE_HEIGHT * (2 - s[i,k] - t[i,k]), name = "Unusable grid cell 4")
    
    # Orientation constraint
    for i in range(num_optgroup1):
        model.addConstr(w[i] == h[i]*((max(optgroup_1[i]['w_h'])/min(optgroup_1[i]['w_h']))*orientation[i]
                                        +(min(optgroup_1[i]['w_h'])/max(optgroup_1[i]['w_h']))*(1-orientation[i])))
    
    # Same orientation for front desks
    model.addConstr(orientation[f]==orientation[b])
    model.addConstr((orientation[f]==1)>>(x[f]==x[b]))
    model.addConstr((orientation[f]==0)>>(y[f]==y[b]))

    # Constraint for object long side againt wall
    for i in range(num_optgroup1):
        for j in range(num_optgroup1):
            if [i, j] == [f,b]:
                model.addConstr((q[i,j]==1)>>(orientation[i]==1))
                model.addConstr((q[i,j]==0)>>(orientation[i]==0))

    # Optimize the model
    model.optimize()
    end_time = time.time()
    result = {}
    unusable_gridcell2 = {}
    unusable_gridcell2.update(unusable_gridcell)

    # Print objective value and runtime
    if model.status == GRB.OPTIMAL:
        print(f"Runtime: {end_time - start_time} seconds")
        print("Optimal solution found!")
        for i in range(num_optgroup1):
            print(f"Object {i}: x={x[i].X}, y={y[i].X}, w={w[i].X}, h={h[i].X}")
            result.update({i:{'x':x[i].X, 'y':y[i].X, 'w':w[i].X, 'h':h[i].X}})
            unusable_gridcell2.update({num_unusable_cells:{'x':x[i].X, 'y':y[i].X, 'w':w[i].X, 'h':h[i].X}})
            num_unusable_cells+=1
        
        # Save space for door opening and lineup sapce for front counter

        num_unusable_cells = len(unusable_gridcell2)

        for i in range(num_optgroup1):
            if i == b:
                if select[i,0].X == 1:
                    unusable_gridcell2.update({num_unusable_cells:{'x':x[i].X+w[i].X+COUNTER_SPACING+w[f].X, 'y':y[i].X, 'w':LINEUP_SPACING, 'h':h[i].X}})
                    num_unusable_cells+=1
                elif select[i,1].X == 1:
                    unusable_gridcell2.update({num_unusable_cells:{'x':x[i].X-(w[f].X + COUNTER_SPACING+LINEUP_SPACING), 'y':y[i].X, 'w':LINEUP_SPACING, 'h':h[i].X}})
                    num_unusable_cells+=1
                elif select[i,2].X == 1:
                    unusable_gridcell2.update({num_unusable_cells:{'x':x[i].X, 'y':y[i].X+h[i].X+COUNTER_SPACING+h[f].X, 'w':w[i].X, 'h':LINEUP_SPACING}})
                    num_unusable_cells+=1
                elif select[i,3].X == 1:
                    unusable_gridcell2.update({num_unusable_cells:{'x':x[i].X, 'y':y[i].X-(h[f].X+COUNTER_SPACING+LINEUP_SPACING), 'w':w[i].X, 'h':LINEUP_SPACING}})
                    num_unusable_cells+=1
            if i == f:
                pass
            else:
                print(f'object:{i}: select[i,0]={select[i,0].X},  select[i,1]={select[i,1].X}, select[i,2]={select[i,2].X}, select[i,3]={select[i,3].X}')
                if select[i,0].X == 1:
                    unusable_gridcell2.update({num_unusable_cells:{'x':x[i].X+w[i].X, 'y':y[i].X, 'w':OPENDOOR_SPACING, 'h':h[i].X}})
                    num_unusable_cells+=1
                elif select[i,1].X == 1:
                    unusable_gridcell2.update({num_unusable_cells:{'x':x[i].X-OPENDOOR_SPACING, 'y':y[i].X, 'w':OPENDOOR_SPACING, 'h':h[i].X}})
                    num_unusable_cells+=1
                elif select[i,2].X == 1:
                    unusable_gridcell2.update({num_unusable_cells:{'x':x[i].X, 'y':y[i].X+h[i].X, 'w':w[i].X, 'h':OPENDOOR_SPACING}})
                    num_unusable_cells+=1
                elif select[i,3].X == 1:
                    unusable_gridcell2.update({num_unusable_cells:{'x':x[i].X, 'y':y[i].X-OPENDOOR_SPACING, 'w':w[i].X, 'h':OPENDOOR_SPACING}})
                    num_unusable_cells+=1
        print(f'Used grid cells in optimization stage 1: {unusable_gridcell2}')

        if select[b,0].X==1:
            counter_placement = 'west'
        elif select[b,1].X==1:
            counter_placement = 'east'
        elif select[b,2].X==1:
            counter_placement = 'north'
        elif select[b,3].X==1:
            counter_placement = 'south'

        
    elif model.status == GRB.INFEASIBLE:
        print("The problem is infeasible. Review your constraints.")
    else:
        print("No solution found.")
        
        model.computeIIS()
        for c in model.getConstrs():
            if c.IISConstr: print(f'\t{c.constrname}: {model.getRow(c)} {c.Sense} {c.RHS}')
        pass

    return result, unusable_gridcell2, counter_placement

def layout_opt_group2(obj_params, AISLE_SPACE, SPACE_WIDTH, SPACE_HEIGHT, unusable_gridcell):
        # Create a Gurobi model
    start_time = time.time()
    model = gp.Model("layout_generation_front desk")
    model.params.NonConvex = 2

    num_objects = len(obj_params)
    num_unusable_cells = len(unusable_gridcell)
    
    optgroup_2 = {}

    temp = 0
    for i in range(num_objects):
        if obj_params[i]['group']==2:
            optgroup_2.update({temp:obj_params[i]})
            temp+=1
    num_optgroup2 = len(optgroup_2)

    for i in range(num_optgroup2):
        if optgroup_2[i]['name']=='貨架區':
            shelf = i
            #print(shelf)
    

    p, q, s, t, orientation = {}, {}, {}, {}, {}
    x, y, w, h, select, T = {}, {}, {}, {}, {}, {}
    # Binary variables
    for i in range(num_optgroup2):
        for j in range(num_optgroup2):
            if i != j:
                p[i, j] = model.addVar(vtype=GRB.BINARY, name=f"p_{i}_{j}")
                q[i, j] = model.addVar(vtype=GRB.BINARY, name=f"q_{i}_{j}")
        for k in range(num_unusable_cells):
            s[i, k] = model.addVar(vtype=GRB.BINARY, name=f"s_{i}_{k}")
            t[i, k] = model.addVar(vtype=GRB.BINARY, name=f"t_{i}_{k}")
        orientation[i] = model.addVar(vtype=GRB.BINARY, name=f"orientation_{i}")

    # Dimension variables
    for i in range(num_optgroup2):
        x[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"x_{i}")
        y[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"y_{i}")
        w[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"w_{i}")
        h[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"h_{i}")

        for k in range(4):
            select[i,k] = model.addVar(vtype=GRB.BINARY, name=f"select_{i,k}")
    
        for j in range(num_optgroup2):
            T[i,j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"T_{i,j}")


    # Set objective
    #model.setObjective(gp.quicksum(w[i]*h[i] for i in range(num_optgroup2)), GRB.MINIMIZE)
    #model.setParam('TimeLimit', 1800)
    model.setObjective(w[shelf]*h[shelf], GRB.MAXIMIZE)
    # Set constraints for general specifications
    # Connectivity constraint
    for i in range(num_optgroup2):
        if not optgroup_2[i]['connect']:
            pass
        else:
            for j in optgroup_2[i]['connect']:
                print(f'Object {i} and Object {j} should be connected')
                model.addConstr(x[i] + w[i] >= x[j] - SPACE_WIDTH*(p[i,j] + q[i,j]), name="Connectivity Constraint 1")
                model.addConstr(y[i] + h[i] >= y[j] - SPACE_HEIGHT*(1 + p[i,j] - q[i,j]), name="Connectivity Constraint 2")
                model.addConstr(x[j] + w[j] >= x[i] - SPACE_WIDTH*(1 - p[i,j] + q[i,j]), name = "Connectivity Constraint 3")
                model.addConstr(y[j] + h[j] >= y[i] - SPACE_HEIGHT*(2 - p[i,j] - q[i,j]), name = "Connectivity Constraint 4")
                model.addConstr(0.5*(w[i]+w[j]) >= T[i,j] + (y[j] - y[i]) - SPACE_WIDTH*(p[i,j] + q[i,j]), name="overlap constraint_18")
                model.addConstr(0.5*(h[i]+h[j]) >= T[i,j] + (x[j] - x[i]) - SPACE_HEIGHT*(2 - p[i,j] - q[i,j]), name="overlap constraint_19")
                model.addConstr(0.5*(w[i]+w[j]) >= T[i,j] + (y[i] - y[j]) - SPACE_WIDTH*(1 - p[i,j] + q[i,j]), name="overlap constraint_20")
                model.addConstr(0.5*(h[i]+h[j]) >= T[i,j] + (x[i] - x[j]) - SPACE_HEIGHT*(1 + p[i,j] - q[i,j]), name="overlap constraint_21")

    # Boundary constraints
    for i in range(num_optgroup2):
        model.addConstr(x[i] + w[i] <= SPACE_WIDTH, name="Boundary constraint for x")
        model.addConstr(y[i] + h[i] <= SPACE_HEIGHT, name="Boundary constraint for y")
    
    # Fixed border constraint
    for i in range(num_optgroup2):
        if not optgroup_2[i]['fixed_wall']:
            print(f'No fixed wall constraint for object {i}')
        elif optgroup_2[i]['fixed_wall']== 'any':
            # 選靠哪面牆
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(optgroup_2[i]['w_h'])-SPACE_WIDTH+1)*select[i,1]+(y[i]+1)*select[i,2]
                            +(y[i]+min(optgroup_2[i]['w_h'])-SPACE_HEIGHT+1)*select[i,3]==1, name='any constraint')
        elif optgroup_2[i]['fixed_wall'] == 'north':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(optgroup_2[i]['w_h'])-SPACE_WIDTH+1)*select[i,1]+(y[i]+1)*select[i,2]
                            +(y[i]+min(optgroup_2[i]['w_h'])-SPACE_HEIGHT+1)*select[i,3]==1, name='any constraint')
            model.addConstr(select[i,2]==1, name="North border constraint")
        elif optgroup_2[i]['fixed_wall']== 'south':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(optgroup_2[i]['w_h'])-SPACE_WIDTH+1)*select[i,1]+(y[i]+1)*select[i,2]
                            +(y[i]+min(optgroup_2[i]['w_h'])-SPACE_HEIGHT+1)*select[i,3]==1, name='any constraint')
            model.addConstr(select[i,3]==1, name="South border constraint")
        elif optgroup_2[i]['fixed_wall']== 'east':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(optgroup_2[i]['w_h'])-SPACE_WIDTH+1)*select[i,1]+(y[i]+1)*select[i,2]
                            +(y[i]+min(optgroup_2[i]['w_h'])-SPACE_HEIGHT+1)*select[i,3]==1, name='any constraint')
            model.addConstr(select[i,1]==1, name="East border constraint")
        elif optgroup_2[i]['fixed_wall']== 'west':
            model.addConstr(select[i,0] + select[i,1] + select[i,2] +select[i,3] == 1)
            # 限制長邊靠牆
            model.addConstr((select[i,0] + select[i,1])*(1-orientation[i]) + (select[i,2] +select[i,3])*orientation[i] == 1)
            model.addConstr((x[i]+1)*select[i,0]+(x[i]+min(optgroup_2[i]['w_h'])-SPACE_WIDTH+1)*select[i,1]+(y[i]+1)*select[i,2]
                            +(y[i]+min(optgroup_2[i]['w_h'])-SPACE_HEIGHT+1)*select[i,3]==1, name='any constraint')
            model.addConstr(select[i,0]==1, name="West border constraint")

    
    # Non-intersecting with aisle constraint
    for i in range(num_optgroup2):
        for j in range(num_optgroup2):
            if not optgroup_2[i]['connect'] and i != j:
                model.addConstr(x[i] + w[i] + AISLE_SPACE <= x[j] + SPACE_WIDTH * (p[i,j] + q[i,j]), name="Non-intersecting Constraint 1")
                model.addConstr(y[i] + h[i] + AISLE_SPACE <= y[j] + SPACE_HEIGHT * (1 + p[i,j] - q[i,j]), name="Non-intersecting Constraint 2")
                model.addConstr(x[j] + w[j] + AISLE_SPACE <= x[i] + SPACE_WIDTH * (1 - p[i,j] + q[i,j]), name = "Non-intersecting Constraint 3")
                model.addConstr(y[j] + h[j] + AISLE_SPACE <= y[i] + SPACE_HEIGHT * (2 - p[i,j] - q[i,j]), name = "Non-intersecting Constraint 4")
            elif i!=j:
                model.addConstr(x[i] + w[i] <= x[j] + SPACE_WIDTH * (p[i,j] + q[i,j]), name="Non-intersecting Constraint 1")
                model.addConstr(y[i] + h[i] <= y[j] + SPACE_HEIGHT * (1 + p[i,j] - q[i,j]), name="Non-intersecting Constraint 2")
                model.addConstr(x[j] + w[j] <= x[i] + SPACE_WIDTH * (1 - p[i,j] + q[i,j]), name = "Non-intersecting Constraint 3")
                model.addConstr(y[j] + h[j] <= y[i] + SPACE_HEIGHT * (2 - p[i,j] - q[i,j]), name = "Non-intersecting Constraint 4")

    # Length constraint
    for i in range(num_optgroup2):
        if i != shelf:
            model.addConstr(w[i]==[min(optgroup_2[i]['w_h']),max(optgroup_2[i]['w_h'])] , name="Length Constraint 1")
            model.addConstr(h[i] == [min(optgroup_2[i]['w_h']), max(optgroup_2[i]['w_h'])], name="Height Constraint 2")
   
    model.addConstr(w[shelf]<=SPACE_WIDTH, name="Shelf area 1")
    model.addConstr(h[shelf]<=SPACE_HEIGHT, name="Shelf area2")

    # Unusable grid cell constraint
    for i in range(num_optgroup2):
        for k in range(num_unusable_cells):
            model.addConstr(x[i] >= unusable_gridcell[k]['x']+ unusable_gridcell[k]['w'] + 1 - SPACE_WIDTH * (s[i,k] + t[i,k]), name="Unusable grid cell 1")
            model.addConstr(unusable_gridcell[k]['x'] >= x[i] + w[i] - SPACE_WIDTH * (1 + s[i,k] - t[i,k]), name="Unusable grid cell 2")
            model.addConstr(y[i] >= unusable_gridcell[k]['y'] + unusable_gridcell[k]['h'] + 1 - SPACE_HEIGHT * (1 - s[i,k] + t[i,k]), name = "Unusable grid cell 3")
            model.addConstr(unusable_gridcell[k]['y'] >= y[i] + h[i] - SPACE_HEIGHT * (2 - s[i,k] - t[i,k]), name = "Unusable grid cell 4")
    # Orientation constraint
    for i in range(num_optgroup2):
        if i!= shelf:
            model.addConstr(w[i] == h[i]*((max(optgroup_2[i]['w_h'])/min(optgroup_2[i]['w_h']))*orientation[i]
                                          +(min(optgroup_2[i]['w_h'])/max(optgroup_2[i]['w_h']))*(1-orientation[i])))
    
    

    # Optimize the model
    model.optimize()
    end_time = time.time()
    result = {}
    shelf_area = {}

    # Print objective value and runtime
    if model.status == GRB.OPTIMAL:
        print(f"Runtime: {end_time - start_time} seconds")
        print("Optimal solution found!")
        for i in range(num_optgroup2):
            print(f"Object {i}: x={x[i].X}, y={y[i].X}, w={w[i].X}, h={h[i].X}")
            result.update({i:{'x':x[i].X, 'y':y[i].X, 'w':w[i].X, 'h':h[i].X}})
            if i == shelf:
                shelf_area.update({'x':x[i].X, 'y':y[i].X, 'w':w[i].X, 'h':h[i].X})
            
    elif model.status == GRB.INFEASIBLE:
        print("The problem is infeasible. Review your constraints.")
    else:
        print("No solution found.")
        
        model.computeIIS()
        for c in model.getConstrs():
            if c.IISConstr: print(f'\t{c.constrname}: {model.getRow(c)} {c.Sense} {c.RHS}')
        pass
    
    return result, shelf_area


def shelf_opt(shelf_area, shelf_spec, counter_placement):
    x, y = shelf_area['x'], shelf_area['y']
    max_width = int(shelf_area['w'])
    max_height = int(shelf_area['h'])
    shelf_placement = KPtest.knapsack_placement(max_width, max_height, shelf_spec, shelf_height)
    shelf_placement = KPtest.add_FF(shelf_placement,shelf_spec,)
    if counter_placement == 'west':
        pass
    elif counter_placement == 'east':
        shelf_placement = flip.vertical(max_width, shelf_placement)
    elif counter_placement == 'north':
        shelf_placement = flip.cw(max_height, max_width, shelf_placement)
    elif counter_placement == 'south':
        shelf_placement = flip.ccw(max_height, max_width, shelf_placement)
    num_shelf = len(shelf_placement)

    for i in range(num_shelf):
        shelf_placement[i]['x'] = shelf_placement[i]['x']+x
        shelf_placement[i]['y'] = shelf_placement[i]['y']+y

    return shelf_placement



def layout_plot(obj_params, result1, result2, shelf_placement, unusable_gridcell):
    num_objects = len(obj_params)
    # Plot opt_group1
    data = result1

    # Define total space dimensions
    total_space = {'width': SPACE_WIDTH, 'height': SPACE_HEIGHT}

    # Create a new figure
    plt.figure(figsize=(8, 8))
    matplotlib.rcParams['font.family'] = ['Heiti TC']
    # Plot total space
    plt.gca().add_patch(plt.Rectangle((0, 0), total_space['width'], total_space['height'], fill=None, edgecolor='blue', label='Total Space'))
    
    optgroup_1 = {}
    
    temp = 0
    for i in range(num_objects):
        if obj_params[i]['group']==1:
            optgroup_1.update({temp:obj_params[i]})
            temp+=1
    num_optgroup1 = len(optgroup_1)
    object_name = {}
    for i in range(num_optgroup1):
        object_name.update({i:optgroup_1[i]['name']})

    # Plot each object
    for object_id, object_info in data.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']

        plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=object_name[object_id]))
        plt.text(x + w/2, y + h/2, object_name[object_id], ha='center', va='center', color='red', fontsize=12)
    
    # Plot opt_group2
    data = result2
    
    optgroup_2 = {}
    
    temp = 0
    for i in range(num_objects):
        if obj_params[i]['group']==2:
            optgroup_2.update({temp:obj_params[i]})
            temp+=1
    num_optgroup2 = len(optgroup_2)
    object_name = {}
    for i in range(num_optgroup2):
        object_name.update({i:optgroup_2[i]['name']})

    # Plot each object
    for object_id, object_info in data.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']
        if object_id ==0:
            '''
            plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=object_name[object_id]))
            print(f'The area of shelf area = {w}x{h}')
            plt.text(x + w/2, y + h/2, object_name[object_id], ha='center', va='center', color='red', fontsize=12)
            '''
            pass
        else:
            plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=object_name[object_id]))
            plt.text(x + w/2, y + h/2, object_name[object_id], ha='center', va='center', color='red', fontsize=12)
    
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

        plt.gca().add_patch(plt.Rectangle((x, y), w, h, fill=None, edgecolor='black', label=object_name[object_id]))
        plt.text(x + w/2, y + h/2, object_name[object_id], ha='center', va='center', color='red', fontsize=12)

    # Plot obstacle
    # Parameters adaptation
    obstacle_positions = [(unusable_gridcell[k]['x'], unusable_gridcell[k]['y']) for k in unusable_gridcell]
    obstacle_dimensions = [(unusable_gridcell[k]['w'], unusable_gridcell[k]['h']) for k in unusable_gridcell]
    for k, (x_u, y_u) in enumerate(obstacle_positions):
        w_u, h_u = obstacle_dimensions[k]
        plt.gca().add_patch(plt.Rectangle((x_u, y_u), w_u, h_u, fill=None, edgecolor='red', label = 'X'))
        plt.text(x_u + w_u/2, y_u + h_u/2, 'x', ha='center', va='center', color='red', fontsize=8)
    # Set plot limits and labels
    plt.xlim(0, total_space['width'])
    plt.ylim(0,total_space['height'])
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Space Layout')

    # Show plot
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()


if __name__ == '__main__':
    doc ='/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/revise.dxf'
    unusable_gridcell, min_x, max_x, min_y, max_y, feasible = get_feasible_area.feasible_area(doc)
    SPACE_WIDTH,SPACE_HEIGHT= max_x-min_x+1, max_y-min_y+1
    #SPACE_WIDTH, SPACE_HEIGHT = get_range.get_rectangle(doc)
    AISLE_SPACE = 100
    COUNTER_SPACING = 110
    OPENDOOR_SPACING = 110
    LINEUP_SPACING = 160
    
    #Define the parameters and variables
    obj_params = {
        0: {'group':2,'w_h': [SPACE_WIDTH,SPACE_HEIGHT], 'connect':[], 'fixed_wall': 'none', 'name':'貨架區'},
        1: {'group':1,'w_h': [465,66], 'connect':[], 'fixed_wall': 'none', 'name':'前櫃檯'},
        2: {'group':1,'w_h': [598,66], 'connect':[], 'fixed_wall': 'any', 'name':'後櫃檯'},
        3: {'group':1,'w_h': [365,270], 'connect':[], 'fixed_wall': 'any', 'name':'WI'}, 
        4: {'group':2,'w_h': [90,66], 'connect':[], 'fixed_wall': 'none', 'name':'雙溫櫃'},
        5: {'group':2,'w_h': [90,66], 'connect':[], 'fixed_wall': 'none', 'name':'單溫櫃'},
        6: {'group':2,'w_h': [90,66], 'connect':[], 'fixed_wall': 'none', 'name':'OC'},
        7: {'group':1,'w_h': [310,225], 'connect':[], 'fixed_wall': 'any', 'name':'RI'},
        8: {'group':1,'w_h': [95,59], 'connect':[], 'fixed_wall': 'any', 'name':'EC'},
        9: {'group':1,'w_h': [190,90], 'connect':[], 'fixed_wall': 'none', 'name':'子母櫃'},
        10: {'group':1,'w_h': [100,85], 'connect':[], 'fixed_wall': 'any', 'name':'ATM'},
        11: {'group':1,'w_h': [83,64], 'connect':[], 'fixed_wall': 'any', 'name':'影印'},
        12: {'group':1,'w_h': [80,55], 'connect':[], 'fixed_wall': 'any', 'name':'KIOSK'}
    }
    # input coordinates for hollowed out spaces and columns

    shelf_spec = [132, 223, 314, 405, 496, 587, 678, 91, 182, 273, 364, 455, 546]
    shelf_height = [78]

    result1, unusable_gridcell2, counter_placement = layout_opt_group1(obj_params,COUNTER_SPACING, SPACE_WIDTH, SPACE_HEIGHT, OPENDOOR_SPACING, LINEUP_SPACING, unusable_gridcell)
    result2, shelf_area = layout_opt_group2(obj_params, AISLE_SPACE, SPACE_WIDTH, SPACE_HEIGHT, unusable_gridcell2)
    shelf_placement = shelf_opt(shelf_area, shelf_spec, counter_placement)
    # draw_dxf(result,"output_dxf/optresult.dxf",SPACE_WIDTH,SPACE_HEIGHT)
    layout_plot(obj_params, result1, result2, shelf_placement, unusable_gridcell)
