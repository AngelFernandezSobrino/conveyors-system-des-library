import simulator
from simulator.stopper import Stopper


class ControllerExample(simulator.ControllerBase):
    def __init__(self, system_description: dict):
        super().__init__(system_description)
