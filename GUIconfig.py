import json
from pathlib import Path

def save_dict(filepath, dict):
    with open(filepath, 'w') as f:
        json.dump(dict, f)

def load_dict(filepath):
    return json.loads(open(filepath).read())

if __name__ == '__main__':
    path = Path(__file__).parent.absolute()

    dict = {
        "t equilibration": 0,
        "E begin": 0,
        "E end": -600,
        "E step": 10,
        "Amplitude": 10,
        "Frequency": 100
    }

    save_dict(f'{path}/config.json', dict)

    loaded_dict = load_dict(f'{path}/config.json')
    print(loaded_dict)