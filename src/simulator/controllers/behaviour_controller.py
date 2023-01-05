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
        self.check_request_functions = []
        self.return_rest_functions = {}

    def check_request(self, stopper_id, data: CheckRequestData):
        if stopper_id not in self.check_request_functions:
            return
        for check_request_function in self.check_request_functions[stopper_id]:
            check_request_function['function'](check_request_function['params'], data)


def delay(params, data: CheckRequestData):
    stopper = data['stopper']
    for stop in stopper.management_stop:
        if not stop:
            stopper.in_event_lock(stopper.output_ids)
    if stopper.request_time == params['time']:
        data['events_register'].push(stopper.in_event_unlock, stopper.output_ids[0], params['time'])
