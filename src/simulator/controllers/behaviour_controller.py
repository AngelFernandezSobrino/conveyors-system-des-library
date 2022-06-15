from typing import TypedDict

import simulator.objects.system
import simulator.helpers.timed_events_manager


class CheckRequestData(TypedDict):
    simulation: simulator.objects.system.SimulationData
    events_register: simulator.helpers.timed_events_manager.TimedEventsManager
    stopper: simulator.objects.stopper.Stopper


class BaseBehaviourController:

    def __init__(self, system_description):
        self.system_description = system_description
        self.external_functions = {}
        self.check_request_functions = {}
        self.return_rest_functions = {}

    def check_request(self, stopper_id, data: CheckRequestData):
        if stopper_id not in self.check_request_functions:
            return
        self.check_request_functions[stopper_id][0](self.check_request_functions[stopper_id][1], data)


def delay(params, data: CheckRequestData):
    stopper = data['stopper']
    stopper.lock(stopper.output_ids[params['output_index']])
    if stopper.request_time == params['time']:
        data['events_register'].push(stopper.unlock, stopper.output_ids[0], params['time'])
