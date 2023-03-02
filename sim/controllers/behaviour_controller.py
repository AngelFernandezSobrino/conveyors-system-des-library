from __future__ import annotations
from typing import TYPE_CHECKING, Callable

import sim.objects.stopper.core

if TYPE_CHECKING:
    import sim.objects.system

import sim.helpers.timed_events_manager

class ParametrizedFunction():

    def __init__(self, function: Callable, params: dict = {}):
        self.function = function
        self.params = params
    
    def __call__(self, context):
        return self.function(context, self.params)


class BaseBehaviourController:
    def __init__(self, system_description):
        self.system_description = system_description
        self.external_functions: dict[str, list[ParametrizedFunction]] = {}
        self.check_request_functions: dict[str, list[ParametrizedFunction]] = {}
        self.return_rest_functions: dict[str, any] = {}


def delay(self: sim.objects.stopper.core.Stopper, params):
    self.input_events.lock(all=True)
    self.events_manager.push(
        sim.helpers.timed_events_manager.Event(
            self.input_events.unlock, (), {"all": True}
        ),
        params["time"],
    )
