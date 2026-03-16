import os
import json
import time
import csv
from dummy_data import data

CLASSES_ROOT_DIR = 'classes'

def create_required_folders():
    folders = ['classes']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def load_config():
    try:
        with open('config.json', 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print('-> Config.json file is missing')
        time.sleep(100)

def _create_required_folders_for_class(class_path):

    folders = ['data', 'results']
    for folder in folders:
        os.makedirs(f'{class_path}/{folder}', exist_ok=True)

def save_formatted_data(data, execute_calculations):
    
    class_name = data['class']['name']
    class_group = data['class']['group']
    class_path = os.path.join(CLASSES_ROOT_DIR, class_name)

    _create_required_folders_for_class(class_path)

    file_path = os.path.join(class_path, f'data/{class_name}_{class_group}.json')

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    execute_calculations(os.path.join(class_path, 'data'))

def save_to_csv(data, file_destination, field_names):
    with open(file_destination, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(data)