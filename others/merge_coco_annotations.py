import os
import json
import shutil
from pathlib import Path

root_dir = r'annotations'
new_images_dir = os.path.join(root_dir + '/output', 'images')
new_results_file = os.path.join(root_dir+ '/output', 'result.json')

os.makedirs(new_images_dir, exist_ok=True)

new_results = {"images": [], "annotations": [], "info": {}, "categories": []}

total_images = 0
image_id_counter = 0
annotation_id_counter = 0

image_id_mapping = {}

for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        filepath = subdir + os.sep + file
        
        if filepath.endswith((".png", ".jpg", ".jpeg")):
            new_path = os.path.join(new_images_dir, file)
            if not os.path.exists(new_path):
                shutil.copy(filepath, new_images_dir)
                total_images+=1

        elif filepath.endswith("result.json"):
            with open(filepath) as f:
                data = json.load(f)
                
                if not new_results['info']:
                    new_results['info'] = data['info']
                if not new_results['categories']:
                    new_results['categories'] = data['categories']
                
                for image in data['images']:
                    old_image_id = image['id']
                    image['id'] = image_id_counter
                    image_id_mapping[old_image_id] = image_id_counter
                    new_results['images'].append(image)
                    image_id_counter += 1
                    
                for annotation in data['annotations']:
                    annotation['id'] = annotation_id_counter
                    annotation['image_id'] = image_id_mapping[annotation['image_id']]
                    new_results['annotations'].append(annotation)
                    annotation_id_counter += 1    

print('Total images: ', total_images)
print('Total images data in json: ', len(new_results['images']))
print('Total annotations in json: ', len(new_results['annotations']))

with open(new_results_file, 'w') as f:
    json.dump(new_results, f, indent=4)