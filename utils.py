import os
import json
import time
import csv
from dummy_data import data
from pathlib import Path
import shutil
import sys

CLASSES_ROOT_DIR = 'classes'

def create_required_folders():
    folders = ['classes']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def load_config():
    """Load configuration from config.json"""    
    
    def get_config_path():
        if getattr(sys, 'frozen', False):
            # Running as exe
            base_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, 'config.json')
    
    config_path = get_config_path()
    
    if not os.path.exists(config_path):
        # Config file doesn't exist - raise error
        error_msg = f"config.json not found at: {config_path}\n\n"
        error_msg += "Please ensure config.json is in the same folder as the application.\n"
        error_msg += "The config file should contain your OpenAI API key."
        raise FileNotFoundError(error_msg)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Validate that the API key exists
        api_key = config.get('app', {}).get('openai_api_key')
        if not api_key:
            error_msg = "OpenAI API key not configured in config.json\n\n"
            error_msg += "Please open config.json and add your OpenAI API key:\n"
            error_msg += '{\n  "app": {\n    "openai_api_key": "your-actual-api-key-here"\n  }\n}'
            raise ValueError(error_msg)
            
        return config
        
    except json.JSONDecodeError:
        error_msg = f"config.json is not valid JSON at: {config_path}\n\n"
        error_msg += "Please check the file format. It should look like:\n"
        error_msg += '{\n  "app": {\n    "openai_api_key": "your-api-key-here"\n  }\n}'
        raise ValueError(error_msg)

def _create_required_folders_for_class(class_path, class_tag):

    folders = ['data', 'results', f'results/{class_tag}']
    for folder in folders:
        os.makedirs(f'{class_path}/{folder}', exist_ok=True)

def save_formatted_data(data, execute_calculations):
    
    class_name = data['class']['name']
    class_group = data['class']['group']

    class_tag = f'{class_name}_{class_group}'
    
    os.makedirs(f'{CLASSES_ROOT_DIR}/{class_name}', exist_ok=True)
    class_path = os.path.join(CLASSES_ROOT_DIR, class_name)

    _create_required_folders_for_class(class_path, class_tag)

    file_path = os.path.join(class_path, f'data/{class_tag}.json')

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    execute_calculations(os.path.join(class_path, 'data'))

def save_to_csv(data, file_destination, field_names):
    with open(file_destination, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(data)

def reset_grading_session():

    folder = Path(CLASSES_ROOT_DIR)

    for item in folder.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()  # Deletes files or symbolic links
        elif item.is_dir():
            shutil.rmtree(item)  # Deletes subdirectories and their contents