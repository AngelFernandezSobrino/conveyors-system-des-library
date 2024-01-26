from __future__ import annotations
from typing import (
    Dict,
    Generic,
    TypeVar,
    TypedDict,
    TYPE_CHECKING,
)

from . import events
from . import states

import desym.objects.stopper

if TYPE_CHECKING:
    from desym.objects.container import Container
    from desym.objects.conveyor.core import Conveyor
    import desym.objects.system
    from desym.external_function import ExternalFunctionController
    from desym.events_manager import TimedEventsManager
    import desym.core
    import desym.objects.stopper


class StopperDescription(TypedDict):
    destiny: list[desym.objects.stopper.StopperId]
    steps: list[int]
    move_behaviour: list[str]
    rest_steps: list[int]
    default_locked: bool
    priority: int


ContentType = TypeVar("ContentType")


class Stopper(Generic[ContentType]):
    def __init__(
        self,
        id: desym.objects.stopper.StopperId,
        description: StopperDescription,
        simulation: desym.core.Simulation,
        external_events_controller: ExternalFunctionController,
        debug,
    ):
        self.id = id
        self.description = description

        # External function to emit events to extenal system
        self.external_events_controller = external_events_controller

        # Globals
        self.simulation: desym.core.Simulation = simulation
        self.timed_events_manager: TimedEventsManager = (
            self.simulation.timed_events_manager
        )

        self.behaviorInfo = BehaviorInfo(
            id,
            self.description,
            self.simulation.description,
        )

        self.output_conveyors: Dict[desym.objects.stopper.StopperId, Conveyor] = {}
        self.input_conveyors: Dict[desym.objects.stopper.StopperId, Conveyor] = {}

        # Container storage pointer
        self.container: Container[ContentType] | None = None

        # Stopper composition objects
        self.input_events: events.InputEvents = events.InputEvents(self)
        self.output_events: events.OutputEvents = events.OutputEvents(self)
        self.states: states.StateController = states.StateController(self)

    def __str__(self) -> str:
        return f"Stopper {self.id}"

    def set_input_conveyors(
        self,
        input_conveyor: Conveyor,
        origin_stopper_id: desym.objects.stopper.StopperId,
    ) -> None:
        if input_conveyor not in self.input_conveyors:
            self.input_conveyors[origin_stopper_id] = input_conveyor

    def set_output_conveyors(
        self,
        output_conveyor: Conveyor,
        destiny_stopper_id: desym.objects.stopper.StopperId,
    ) -> None:
        if output_conveyor not in self.output_conveyors:
            self.output_conveyors[destiny_stopper_id] = output_conveyor


class BehaviorInfo:
    def __init__(self, stopper_id, stopper_description, simulation_description):
        self.default_stopped = stopper_description["default_locked"]
        self.output_stoppers_ids = stopper_description["destiny"]
        self.move_steps = {
            self.output_stoppers_ids[k]: v
            for k, v in enumerate(stopper_description["steps"])
        }
        self.return_available_steps = {
            self.output_stoppers_ids[k]: v
            for k, v in enumerate(stopper_description["rest_steps"])
        }
        self.move_behaviour = {
            self.output_stoppers_ids[k]: v
            for k, v in enumerate(stopper_description["move_behaviour"])
        }
        self.input_stoppers_ids: list[desym.objects.stopper.StopperId] = []
        for external_stopper_id, stopper_info in simulation_description.items():
            if stopper_id in stopper_info["destiny"]:
                self.input_stoppers_ids += [external_stopper_id]
