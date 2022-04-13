from simulator.stopper import StopperInfo

system_description_example_old: dict[str, StopperInfo] = {
    '0': {
        'destiny': ['1'],
        'steps': [8],
        'move_behaviour': ['fast'],
        'rest_steps': [1],
        'default_locked': False
    },
    '1': {
        'destiny': ['2'],
        'steps': [8],
        'move_behaviour': ['fast'],
        'rest_steps': [1],
        'default_locked': False
    },
    '2': {
        'destiny': ['3'],
        'steps': [8],
        'move_behaviour': ['fast'],
        'rest_steps': [1],
        'default_locked': False
    },
    '3': {
        'destiny': ['4'],
        'steps': [8],
        'move_behaviour': ['fast'],
        'rest_steps': [1],
        'default_locked': False
    }
}

system_description_example: dict[str, StopperInfo] = {
    "0": {"destiny": "[1]", "steps": "[8]", "move_behaviour": "['fast']", "rest_steps": "[1]",
          "default_locked": "False"},
    "1": {"destiny": "[2]", "steps": "[8]", "move_behaviour": "['fast']", "rest_steps": "[1]",
          "default_locked": "False"},
    "2": {"destiny": "[3]", "steps": "[8]", "move_behaviour": "['fast']", "rest_steps": "[1]",
          "default_locked": "False"},
    "3": {"destiny": "[4]", "steps": "[8]", "move_behaviour": "['fast']", "rest_steps": "[1]",
          "default_locked": "False"},
    "4": {"destiny": "[5]", "steps": "[8]", "move_behaviour": "['fast']", "rest_steps": "[1]",
          "default_locked": "False"}
}
