from stopper import StopperInfo

system_description_example: dict[str, StopperInfo] = {
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
        'destiny': ['0'],
        'steps': [8],
        'move_behaviour': ['fast'],
        'rest_steps': [1],
        'default_locked': False
    }
}