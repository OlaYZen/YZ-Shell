import json
import os
from fabric.utils import get_relative_path

class PrivateData:
    def __init__(self) -> None:
        _location = ""
        
        try:
            path: str = get_relative_path(path='../personal_config.json')
            if os.path.exists(path):
                with open(file=path, mode='r') as f:
                    data = json.load(fp=f)
                    _location = data.get("location", _location)
            else:
                print("File not found: personal_config.json")
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error reading personal_config.json, using default location")
        
        self._location = str(_location)

    def get_location(self) -> str:
        return f'{self._location}'

    location: property = property(fget=get_location)
