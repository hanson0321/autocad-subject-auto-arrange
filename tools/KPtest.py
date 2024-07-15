import matplotlib.pyplot as plt
import matplotlib.patches as patches

def knapsack(max_width, max_height, items, gap):
    # DP table initialization
    dp = [[0] * (max_height + 1) for _ in range(max_width + 1)]
    keep = [[[] for _ in range(max_height + 1)] for _ in range(max_width + 1)]
    
    for item_key in items:
        width, height, count = items[item_key]
        # 最大化貨架個數
        #value = count
        # 最大化貨架面積
        value = width * height * count 
        adjusted_width = width + gap
        adjusted_height = height + gap
        for w in range(max_width, adjusted_width - 1, -1):
            for h in range(max_height, adjusted_height - 1, -1):
                if dp[w - adjusted_width][h - adjusted_height] + value > dp[w][h]:
                    dp[w][h] = dp[w - adjusted_width][h - adjusted_height] + value
                    keep[w][h] = keep[w - adjusted_width][h - adjusted_height] + [(item_key, width, height, count)]
    
    return dp[max_width][max_height], keep[max_width][max_height]

def visualize_placement(max_width, max_height, placement, gap):
    current_x = 0
    current_y = 0
    coordinates = {}

    index = 0
    for item in placement:
        item_key, width, height, count = item
        for _ in range(count):
            if current_x + width + gap > max_width:
                current_x = 0
                current_y += height + gap
            if current_y + height + gap > max_height:
                break
            coordinates[index] = {"type": item_key, "x": current_x, "y": current_y, "width": width, "height": height}
            index += 1
            current_x += width + gap

    
    return coordinates

def knapsack_placement(max_width, max_height, gap, items):

    max_value, placement = knapsack(max_width, max_height, items, gap)
    
    print(f"Max racks amount: {max_value}")
    print("Solution:")
    for item in placement:
        item_key, width, height, count = item
        print(f"Type: {item_key}, Size: {width}x{height}, Amount: {count}")
    
    coordinates = visualize_placement(max_width, max_height, placement, gap)
    shelf_placement ={}
    print("Coordinates of placed items:")
    for key, coord in coordinates.items():
        shelf_placement.update({key:{'x': coord['x'], 'y': coord['y'],'w': coord['width'], 'h':coord['height']}})
    print(shelf_placement)

    return shelf_placement

if __name__ == "__main__":
    knapsack_placement()
