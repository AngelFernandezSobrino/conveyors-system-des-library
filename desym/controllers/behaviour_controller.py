from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Any

import desym.objects.stopper.core

if TYPE_CHECKING:
    import desym.objects.system

import desym.helpers.timed_events_manager

class ParametrizedFunction():

    def __init__(self, function: Callable, params: dict = {}):
        self.function = function
        self.params = params
    
    def __call__(self, context):
        return self.function(context, self.params)


class BaseBehaviourController:
    def __init__(self, system_description):
        self.system_description = system_description
        self.external_functions: dict[desym.helpers.timed_events_manager.Step, list[ParametrizedFunction]] = {}
        self.check_request_functions: dict[desym.objects.stopper.core.StopperId, list[ParametrizedFunction]] = {}
        self.return_rest_functions: dict[desym.objects.stopper.core.StopperId, Any] = {}


def delay(self: desym.objects.stopper.core.Stopper, params):
    self.input_events.lock(all=True)
    self.events_manager.push(
        desym.helpers.timed_events_manager.Event(
            callable=self.input_events.unlock, args=(), kwargs={"all": True}
        ),
        params["time"],
    )
