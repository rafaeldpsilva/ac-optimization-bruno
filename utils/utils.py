import json
import sys
sys.path.append('.')

def get_config():
    with open('./config/config.json') as config_file:
        return json.load(config_file)
