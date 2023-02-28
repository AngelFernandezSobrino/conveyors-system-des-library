from __future__ import annotations
from typing import TYPE_CHECKING, Callable
from typing import TypedDict

import sim.objects.stopper.core

if TYPE_CHECKING:
    import sim.objects.system

import sim.helpers.timed_events_manager

class CheckRequestFunction(TypedDict):
    function: Callable
    params: dict


class BaseBehaviourController:
    def __init__(self, system_description):
        self.system_description = system_description
        self.external_functions = {}
        self.check_request_functions: dict[str, list[CheckRequestFunction]] = {}
        self.return_rest_functions: dict[str, any] = {}


def delay(self: sim.objects.stopper.core.Stopper, params):
    self.input_events.lock(all=True)
    self.events_manager.push(
        sim.helpers.timed_events_manager.Event(
            self.input_events.unlock, (), {"all": True}
        ),
        params["time"],
    )
