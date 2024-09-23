def mirror_vertical(rect, total_width):
    return {'x': total_width - rect['x'] - rect['w'], 'y': rect['y'], 'w': rect['w'], 'h': rect['h'],'name':rect['name']}

def mirror_horizontal(rect, total_height):
    return {'x': rect['x'], 'y': total_height - rect['y'] - rect['h'], 'w': rect['w'], 'h': rect['h'],'name':rect['name']}

def mirror_both(rect, total_width, total_height):
    return {'x': total_width - rect['x'] - rect['w'], 'y': total_height - rect['y'] - rect['h'], 'w': rect['w'], 'h': rect['h'],'name':rect['name']}

def rotate_counterclockwise(rect, total_width, total_height):
    return {'x': rect['y'], 'y': total_width - rect['x'] - rect['w'], 'w': rect['h'], 'h': rect['w'],'name':rect['name']}

def rotate_clockwise(rect, total_width, total_height):
    return {'x': total_height - rect['y'] - rect['h'], 'y': rect['x'], 'w': rect['h'], 'h': rect['w'],'name':rect['name']}



def vertical(total_width, shelf_placement):
    vertical_mirrored = {k: mirror_vertical(v, total_width) for k, v in shelf_placement.items()}
    return vertical_mirrored

def horizontal(total_height, shelf_placement):
    horizontal_mirrored = {k: mirror_horizontal(v, total_height) for k, v in shelf_placement.items()}
    return horizontal_mirrored

def both(total_width, total_height, shelf_placement):
    both_mirrored = {k: mirror_both(v, total_width, total_height) for k, v in shelf_placement.items()}
    return both_mirrored

def ccw(total_width, total_height, shelf_placement):
    counterclockwise_rotated = {k: rotate_counterclockwise(v, total_width, total_height) for k, v in shelf_placement.items()}
    return counterclockwise_rotated

def cw(total_width, total_height, shelf_placement):
    clockwise_rotated = {k: rotate_clockwise(v, total_width, total_height) for k, v in shelf_placement.items()}
    return clockwise_rotated