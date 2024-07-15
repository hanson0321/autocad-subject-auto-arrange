def placement_width(total_length, shelves):
    shelves.sort(reverse=True)
    num_shelves = len(shelves)
    SHELF_SPACING_WIDTH = 120

    # Initialize DP table
    DP = [0] * (total_length + 1)

    # Fill DP table
    for j in range(1, total_length + 1):
        for i in range(num_shelves):
            shelf_duration = shelves[i]
            effective_duration = shelf_duration + SHELF_SPACING_WIDTH
            if j >= effective_duration:
                DP[j] = max(DP[j], DP[j - effective_duration] + shelf_duration)

    # Backtracking to find the selected shelves
    shelf_x = []
    j = total_length
    while j > 0:
        for i in range(num_shelves):
            shelf_duration = shelves[i]
            effective_duration = shelf_duration + SHELF_SPACING_WIDTH
            if j >= effective_duration and DP[j] == DP[j - effective_duration] + shelf_duration:
                shelf_x.append(shelf_duration)
                j -= effective_duration
                break
        else:
            break  # No more shelves can fit in the remaining space
    for i in range(num_shelves):
        if total_length-(DP[total_length]+SHELF_SPACING_WIDTH*(len(shelf_x))) >= shelves[i]:
            print(shelves[i])
            shelf_x.append(shelves[i])
            result_x = DP[total_length]+shelves[i]
            break
        else:
            result_x = DP[total_length]


    shelf_x.reverse()
    print("Selected shelves:", shelf_x)
    print("Total shelf space:", result_x)
    return shelf_x

def placement_height(total_length, shelves):
    # shelf durations (in length)
    num_shelves = len(shelves)
    SHELF_SPACING_HEIGHT = 110

    # Initialize DP table
    DP = [0] * (total_length + 1)

    # Fill DP table
    for j in range(1, total_length + 1):
        for i in range(num_shelves):
            shelf_duration = shelves[i]
            effective_duration = shelf_duration + SHELF_SPACING_HEIGHT
            if j >= effective_duration:
                DP[j] = max(DP[j], DP[j - effective_duration] + shelf_duration)

    # Backtracking to find the selected shelves
    shelf_y = []
    j = total_length
    while j > 0:
        for i in range(num_shelves):
            shelf_duration = shelves[i]
            effective_duration = shelf_duration + SHELF_SPACING_HEIGHT
            if j >= effective_duration and DP[j] == DP[j - effective_duration] + shelf_duration:
                shelf_y.append(shelf_duration)
                j -= effective_duration
                break
        else:
            break  # No more shelves can fit in the remaining space

    for i in range(num_shelves):
        if total_length-(DP[total_length]+SHELF_SPACING_HEIGHT*(len(shelf_y))) >= shelves[i]:
            print(shelves[i])
            shelf_y.append(shelves[i])
            result_y = DP[total_length]+shelves[i]
            break
        else:
            result_y = DP[total_length]


    shelf_y.reverse()
    print("Selected shelves:", shelf_y)
    print("Total shelf space:", result_y)
    return shelf_y

def knapsack_placement(W, H, shelf_spec, shelf_height):
    shelf_x = placement_width(W, shelf_spec)
    shelf_y = placement_height(H, shelf_height)
    placement = {}
    shelf_amount = len(shelf_x)*len(shelf_y)
    tmp_y = 0
    i = 0
    for j in range(len(shelf_y)):
        tmp_x = 0
        for k in range(len(shelf_x)):        
            tmp_dict = {'x':tmp_x, 'y':tmp_y, 'w':shelf_x[k], 'h':78}
            placement.update({i:tmp_dict})
            tmp_x+=shelf_x[k]+110
            i+=1
        tmp_y+=188     
    print(placement)
    return placement

if __name__ =='__main__':
    max_width, max_height = 1127, 490
    shelf_spec = [132, 223, 314, 405, 496, 587, 678, 91, 182, 273, 364, 455, 546]
    shelf_height = [78]
    knapsack_placement(max_width, max_height, shelf_spec, shelf_height)
