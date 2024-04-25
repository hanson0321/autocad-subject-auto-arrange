def normalize_edge(edge):
    """ Normalize the edge such that the smaller vertex comes first. """
    return tuple(sorted(edge))

def compute_slope_and_intercept(v1, v2):
    """ Compute the slope and y-intercept of the line through v1 and v2. Return None for vertical lines. """
    (x1, y1), (x2, y2) = v1, v2
    if x1 == x2:  # Vertical line
        return None, x1  # Use x-coordinate as "intercept" for vertical lines
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    return slope, intercept

def merge_edges(edges):
    from collections import defaultdict

    # Group edges by their line (slope and intercept)
    lines = defaultdict(list)
    for edge in edges:
        edge = normalize_edge(edge)
        key = compute_slope_and_intercept(*edge)
        lines[key].append(edge)

    # Merge contiguous edges on the same line
    merged_edges = []
    for (slope, intercept), group in lines.items():
        # Sort edges by the first vertex (necessary for merging)
        group.sort()
        current_start, current_end = group[0]

        for start, end in group[1:]:
            if current_end == start:  # Contiguous edges
                current_end = end  # Extend the current edge
            else:
                merged_edges.append((current_start, current_end))
                current_start, current_end = start, end
        
        # Add the last merged edge
        merged_edges.append((current_start, current_end))

    return merged_edges
'''
# Example input
edges = [
    [(1, 2), (2, 2)],
    [(2, 2), (4, 2)],
    [(4, 2), (6, 2)],
    [(3, 5), (4, 5)],
    [(4, 5), (5, 5)],
    [(8, 9), (10,11)],
    [(8,3),(84,3)],
    [(84,3), (85,3)]
]

# Merging the edges
result = merge_edges(edges)
print(result)
'''