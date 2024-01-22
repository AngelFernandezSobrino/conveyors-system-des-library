from __future__ import annotations
from ossaudiodev import control_labels
from typing import TYPE_CHECKING, Callable, Any

if TYPE_CHECKING:
    import desym.objects.stopper.core
    from desym.objects.stopper.core import Stopper
    import desym.objects.system

import desym.helpers.timed_events_manager


class ParametrizedFunction:
    def __init__(self, function: Callable, params: dict = {}):
        self.function = function
        self.params = params

    def __call__(self, context):
        return self.function(context, self.params)


class BaseBehaviourController:
    def __init__(self, system_description):
        self.system_description = system_description
        self.external_functions: dict[
            desym.helpers.timed_events_manager.Step, list[ParametrizedFunction]
        ] = {}
        self.check_request_functions: dict[
            Stopper.StopperId, list[ParametrizedFunction]
        ] = {}
        self.return_rest_functions: dict[Stopper.StopperId, Any] = {}


def delay(self: desym.objects.stopper.core.Stopper, params):
    for conveyor in self.output_conveyors:
        self.input_events.control_lock(conveyor.id)
        self.events_manager.push(
            desym.helpers.timed_events_manager.Event(
                callable=self.input_events.control_unlock,
                args=(conveyor.id,),
                kwargs={"all": True},
            ),
            params["time"],
        )
