import json

def json_save(data):

# Convert the data into a more JSON-friendly format
    json_data = [
        [{"x": point[0], "y": point[1]} for point in segment]
        for segment in data
    ]

    # Serialize the data structure to a JSON formatted string
    json_string = json.dumps(json_data, indent=4)

    # Print the JSON string
    print(json_string)

    # Optionally, write the JSON string to a file
    with open('geometry_data.json', 'w') as file:
        file.write(json_string)

def json_open(file_path):
    with open(file_path, 'r') as file:
        json_string = file.read()

    # Deserialize the JSON string back to a Python list of dictionaries
    json_data = json.loads(json_string)

    # Corrected: Convert the list of dictionaries back to the original list of tuples format
    original_data = [
        tuple((point['x'], point['y']) for point in segment)
        for segment in json_data
    ]
    return original_data
