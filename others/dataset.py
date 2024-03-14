import os
import json

# Function to load JSON files from a folder
def load_jsons_from_folder(folder_path):
    json_data = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            with open(os.path.join(folder_path, filename), 'r') as f:
                data = json.load(f)
                json_data.extend(data['annotations'])
    return json_data

# Function to convert loaded JSON data to the desired format
def convert_to_desired_format(json_data):
    converted_data = []
    for item in json_data:
        text = item[0]
        entities = [(start, end, label) for start, end, label in item[1]['entities']]
        converted_data.append((text, {"entities": entities}))
    return converted_data

# Path to the folder containing JSON files
folder_path = r'data\dataset\annotations'

# Load JSON files from the folder
json_data = load_jsons_from_folder(folder_path)

# Convert loaded JSON data to the desired format
converted_data = convert_to_desired_format(json_data)

# Print the result
print(converted_data)