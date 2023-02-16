from __future__ import annotations
from typing import TYPE_CHECKING
from typing import TypedDict

import sim.objects.stopper.core

if TYPE_CHECKING:
    import sim.objects.system

import sim.helpers.timed_events_manager


class CheckRequestData(TypedDict):
    simulation: sim.objects.system.SimulationData
    events_register: sim.helpers.timed_events_manager.TimedEventsManager
    stopper: sim.objects.stopper.core.Stopper


class BaseBehaviourController:
    def __init__(self, system_description):
        self.system_description = system_description
        self.external_functions = {}
        self.check_request_functions = {}
        self.return_rest_functions = {}

    def check_request(self, stopper_id, data: CheckRequestData):
        if stopper_id not in self.check_request_functions:
            return
        for check_request_function in self.check_request_functions[stopper_id]:
            check_request_function["function"](check_request_function["params"], data)


def delay(params, data: CheckRequestData):
    stopper = data["stopper"]
    stopper.input_events.lock(all=True)
    data["events_register"].push(
        sim.helpers.timed_events_manager.Event(
            stopper.input_events.unlock, (), {"all": True}
        ),
        params["time"],
    )
