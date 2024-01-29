from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from desim.objects.stopper.core import StopperDescription

system_description_example: dict[str, StopperDescription] = {
    "0": {
        "destiny": ["1"],
        "steps": [8],
        "move_behaviour": ["fast"],
        "rest_steps": [1],
        "default_locked": False,
        "priority": 0,
    },
    "1": {
        "destiny": ["2"],
        "steps": [8],
        "move_behaviour": ["fast"],
        "rest_steps": [1],
        "default_locked": False,
        "priority": 0,
    },
    "2": {
        "destiny": ["3"],
        "steps": [8],
        "move_behaviour": ["fast"],
        "rest_steps": [1],
        "default_locked": False,
        "priority": 0,
    },
    "3": {
        "destiny": ["0"],
        "steps": [8],
        "move_behaviour": ["fast"],
        "rest_steps": [1],
        "default_locked": False,
        "priority": 0,
    },
}
