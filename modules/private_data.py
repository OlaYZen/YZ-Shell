from fabric.utils import get_relative_path

class PrivateData:
    def __init__(self) -> None:
        self._location = ""

    def get_location(self) -> str:
        return f'{self._location}'

    location: property = property(fget=get_location)
