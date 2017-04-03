import json

from .func import Promise


class JSONEncoder(json.JSONEncoder):
    """JSONEncoder subclass knowing how to work with lazy objects"""

    def default(self, o):
        if isinstance(o, Promise):
            return str(o)
        return o
