import ezdxf
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import json
from shapely.geometry import LineString
from tools import get_feasible_area


# Optional: Layer Colors
def get_layer_colors():
    """
    Returns a dictionary mapping layer names to colors.
    
    Optional:
    This function is only needed if you plan to visualize the DXF layers with specific colors.

    Returns:
    dict: A dictionary where keys are layer names and values are colors.
    """
    return {
        'door': 'red',
        'feasible_area': 'gray',
        'other': 'blue',
        'pillar': 'green',
        'solid_wall': 'orange',
        'window': 'magenta'
    }

# Essential Function: Extract Layer Coordinates
def extract_layer_coordinates(dxf_file, layers_to_draw):
    """
    Extracts the coordinates of entities in the specified layers from the DXF document.

    Parameters:
    dxf_file (str): The path to the DXF file.
    layers_to_draw (list): List of layer names to extract.

    Returns:
    dict: A dictionary where keys are layer names and values are lists of coordinates.
    """
    doc = ezdxf.readfile(dxf_file)  # Read the DXF file
    msp = doc.modelspace()  # Get all entities in the modelspace
    
    layer_coordinates = {layer: [] for layer in layers_to_draw}  # Initialize coordinate lists for each layer
    
    # Initialize min_x and min_y with positive infinity
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    # Iterate through all entities in the document
    for entity in doc.entities:
        # Check if the entity belongs to the 'feasible_area' layer
        if entity.dxf.layer == 'feasible_area':
            x1 = entity.dxf.start[0]
            y1 = entity.dxf.start[1]
            x2 = entity.dxf.end[0]
            y2 = entity.dxf.end[1]
            # Update min_x and min_y to determine the boundaries of the shapes
            min_x, max_x, min_y, max_y = get_feasible_area.check_region(x1, y1, min_x, max_x, min_y, max_y)
            min_x, max_x, min_y, max_y = get_feasible_area.check_region(x2, y2, min_x, max_x, min_y, max_y)

    # Extract coordinates for specified layers
    for entity in msp:
        if entity.dxf.layer in layers_to_draw:
            if entity.dxftype() == 'LINE':  # If the entity is a line
                start = entity.dxf.start
                end = entity.dxf.end
                # Adjust the line coordinates relative to min_x and min_y
                layer_coordinates[entity.dxf.layer].append(([start.x - min_x, start.y - min_y], [end.x - min_x, end.y - min_y]))
            elif entity.dxftype() == 'LWPOLYLINE':  # If the entity is a polyline
                points = entity.get_points('xy')
                # Adjust each point in the polyline relative to min_x and min_y
                adjusted_points = [(x - min_x, y - min_y) for x, y in points]
                layer_coordinates[entity.dxf.layer].append(adjusted_points)
    
    return layer_coordinates  # Return the extracted layer coordinates

# Optional: Visualization
def draw_dxf_layers(layer_coordinates):
    """
    Draws the specified layer coordinates.
    
    Optional:
    This function is only needed if you plan to visualize the DXF layers.


    Parameters:
    layer_coordinates (dict): A dictionary where keys are layer names and values are lists of coordinates.
    """
    layer_colors = get_layer_colors()  # Get the colors for the layers

    # Create the plot area
    fig, ax = plt.subplots()

    # Draw the elements of each layer
    for layer, coordinates in layer_coordinates.items():
        color = layer_colors.get(layer, 'black')  # Set the color
        for coord in coordinates:
            if isinstance(coord[0], tuple):  # If the entity is a polygon
                polyline = patches.Polygon(coord, closed=True, edgecolor=color, fill=False, label=layer)
                ax.add_patch(polyline)
            else:  # If the entity is a line
                ax.plot([coord[0][0], coord[1][0]], [coord[0][1], coord[1][1]], color=color, label=layer)

    # Remove duplicate labels in the legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    
    # Set the aspect ratio of the plot
    ax.set_aspect('equal')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('DXF Layer Visualization')
    plt.grid(True)
    plt.legend(by_label.values(), by_label.keys(), loc='upper left')
    
    # Display the plot
    plt.show()
    
# Essential Function: Process DXF File and Generate Dictionary
def process_dxf(dxf_file, layers_to_draw):
    """
    Process the DXF file to extract layer coordinates and convert them into a dictionary with LineString objects.

    Parameters:
    dxf_file (str): The path to the DXF file.
    layers_to_draw (list): List of layer names to extract.

    Returns:
    dict: A dictionary containing the LineString objects and their types.
    """
    layer_coordinates = extract_layer_coordinates(dxf_file, layers_to_draw)  # Extract the layer coordinates
    
    wall_edges = layer_coordinates.get('solid_wall', [])
    window_edges = layer_coordinates.get('window', [])
    door_edges = layer_coordinates.get('door', [])
    
    edge_dictionary = {}

    # Convert wall edges to LineString objects and store in the dictionary
    for i, edge in enumerate(wall_edges):
        line = LineString(edge)
        edge_dictionary[i] = {'edge': line, 'type': 'wall'}

    # Convert window edges to LineString objects and store in the dictionary
    for i, edge in enumerate(window_edges, start=len(wall_edges)):
        line = LineString(edge)
        edge_dictionary[i] = {'edge': line, 'type': 'window'}

    # Convert door edges to LineString objects and store in the dictionary
    for i, edge in enumerate(door_edges, start=len(wall_edges) + len(window_edges)):
        line = LineString(edge)
        edge_dictionary[i] = {'edge': line, 'type': 'door'}

    return edge_dictionary  # Return the dictionary containing LineString objects and their types

# Main Function
def main():
    """
    The main function to execute the DXF visualization.
    """
    doc = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/revise_v1.dxf'
    layers_to_draw = ['solid_wall', 'window', 'door']  # List of layers to extract and draw
    
    edge_dictionary = process_dxf(doc, layers_to_draw)  # Process the DXF file and generate the dictionary

    for idx, data in edge_dictionary.items():
        print(f"{idx}: {data}")  # Output the contents of the dictionary
    
    # (Optional) Visualization
    # layer_coordinates = extract_layer_coordinates(doc, layers_to_draw)
    # draw_dxf_layers(layer_coordinates)

if __name__ == "__main__":
    main()
