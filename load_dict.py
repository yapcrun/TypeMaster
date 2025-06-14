import json
from os.path import exists
def save_dict(d, filename):
    """Save a dictionary to a file as JSON."""
    with open(filename, 'w') as f:
        json.dump(d, f)

def load_dict(filename):
    """Load a dictionary from a JSON file."""
    if not exists(filename): return None
    with open(filename, 'r') as f:
        return json.load(f)