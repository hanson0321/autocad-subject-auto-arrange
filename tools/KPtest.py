from itertools import combinations_with_replacement

# List of shelves with (width, length, number)
shelves = [(132, 78, 3), (223, 78, 5), (314, 78, 7), (587, 78, 13), (678,78,15), (91,78,2),(182,78,4),(273,78,6),(364,78,8),(455,78,10),(546,78,12),(637,78,14)]

# Priority shelves that must be included (width, length, number)
priority_shelves = [ (405, 78, 9), (496, 78, 11)]

# List of non-numbered shelves with (width, length)
non_numbered_shelves = [(300, 66), (360, 66), (420, 66)]  # Different sizes to choose from

# Minimum and maximum sum of numbers
target_min = 25
target_max = 35

# Available space dimensions (space width and length constraint)
space_width = 500  # Width of the space (cm)
space_length = 1000  # Length of the space (cm)

# Required gap between shelves in cm
gap_between_shelves = 110

# Function to find the combination that maximizes the number of shelves while keeping the sum between 25 and 35
def find_max_combinations_with_repetition(shelves, priority_shelves, target_min=25, target_max=35):
    best_combination = None
    max_total = 0
    area = 0
    
    # Check for combinations with repetition
    for r in range(1, 20):  # Increase range if you expect higher repetitions
        for combo in combinations_with_replacement(priority_shelves, r):
            total_sum = sum(shelf[2] for shelf in combo)
            if target_min <= total_sum <= target_max:
                if total_sum > max_total:  # Update if this combination has a higher total sum
                    max_total = total_sum
                    for c in combo:
                        area += c[0]*c[1]
                    if area <=space_length*space_width*(5/6):
                        best_combination = combo
                    
    return best_combination

# Function to select the largest non-numbered shelf that fits in the available space
def select_largest_non_numbered_shelf(non_numbered_shelves, space_width, space_length):
    for shelf in sorted(non_numbered_shelves, reverse=True, key=lambda x: x[0] * x[1]):  # Sort by area (width * length)
        width, length = shelf
        if width <= space_width and length <= space_length:
            return shelf
    return None  # If no shelf fits

# Function to organize shelves into rows, checking both width and length constraints
# Includes the chosen non-numbered shelf
def organize_into_rows(shelves, non_numbered_shelf, space_width, space_length, gap_between_shelves):
    rows = []
    current_row = []
    current_row_width = 0
    current_row_length = 0
    # Add the non-numbered shelf first
    width, length = non_numbered_shelf
    current_row.append((width, length, 'Non-numbered'))  # Mark it as non-numbered
    current_row_width += width
    current_row_length = length  # Set row length to this shelf's length

    # Organize other shelves
    for shelf in shelves:
        length, width, number = shelf

        # Check if the shelf fits within the space's width and length
        if (space_length-(current_row_length + gap_between_shelves)) >= length and (space_width-(current_row_width + gap_between_shelves)):
            current_row.append(shelf)
            current_row_length += length# Update current row length based on the longest shelf
        else:
            # Move to next row if it doesn't fit
            rows.append(current_row)
            current_row = [shelf]
            current_row_width += width+gap_between_shelves  # Start fresh with new row (no gap on the left of first shelf)
            current_row_length = length  # Reset row length to the length of the current shelf
    
    # Append the last row if there are any shelves left
    if current_row:
        rows.append(current_row)
    return rows

def shelf_placing(shelves, priority_shelves, non_numbered_shelves, space_width, space_length, gap_between_shelves):
    # Minimum and maximum sum of numbers
    target_min = 25
    target_max = 35
    # Find the combination with the maximum total number of shelves
    chosen_shelves = find_max_combinations_with_repetition(shelves, priority_shelves, target_min, target_max)

    # Choose the largest non-numbered shelf that fits
    chosen_non_numbered_shelf = select_largest_non_numbered_shelf(non_numbered_shelves, space_width, space_length)
    
    # If there is a valid combination, organize it into rows
    rows = organize_into_rows(chosen_shelves, chosen_non_numbered_shelf, space_width, space_length, gap_between_shelves)
    
    i = 0
    tmp_x = 0
    tmp_y = 0
    shelf_placement = {}
    for row in rows:
        for r in row:
            shelf_placement.update({i:{'x':tmp_x, 'y':tmp_y, 'w':r[0],'h':r[1]}})
            tmp_x += r[0]+110
            i += 1
        tmp_y += 188
        tmp_x = 0

    return shelf_placement

if __name__ == '__main__':

    # Find the combination with the maximum total number of shelves
    chosen_shelves = find_max_combinations_with_repetition(shelves, priority_shelves, target_min, target_max)

    # Choose the largest non-numbered shelf that fits
    chosen_non_numbered_shelf = select_largest_non_numbered_shelf(non_numbered_shelves, space_width, space_length)

    if chosen_non_numbered_shelf:
        # print(f"Chosen non-numbered shelf (largest that fits): {chosen_non_numbered_shelf}")
        
        # If there is a valid combination, organize it into rows
        rows = organize_into_rows(chosen_shelves, chosen_non_numbered_shelf, space_width, space_length, gap_between_shelves)
        
        # print("Chosen Shelves (maximized with priority and repetition):", chosen_shelves)
        # print(f"Total number sum: {sum(shelf[2] for shelf in chosen_shelves)}")
        # print("Organized Rows (including non-numbered shelf):")
        for idx, row in enumerate(rows):
            print(f"Row {idx + 1}: {row}")
    else:
        print("No non-numbered shelf fits in the available space.")

