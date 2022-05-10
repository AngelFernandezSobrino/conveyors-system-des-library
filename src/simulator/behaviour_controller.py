from typing import TypedDict

import simulator.objects.system
import simulator.helpers.timed_events_manager


class CheckRequestData(TypedDict):
    simulation: simulator.objects.system.SimulationData
    events_register: simulator.helpers.timed_events_manager.TimedEventsManager


class BehaviourController:

    def __init__(self, system_description):
        self.system_description = system_description
        self.external_functions = {}
        self.check_request_functions = {}

    def check_request(self, stopper_id, data: CheckRequestData):
        if stopper_id not in self.check_request_functions:
            return
        self.check_request_functions[stopper_id](data)
