import simulator
from simulator.stopper import Stopper


class ControllerExample(simulator.ControllerBase):
    def __init__(self, system_description: dict):
        super().__init__(system_description)

    def check_request_stopper_1(self, simulation_data: dict[str, Stopper]):
        if simulation_data['1'].request_time < 10:
            simulation_data['1'].lock()
        else:
            simulation_data['1'].unlock()
