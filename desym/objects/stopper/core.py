from __future__ import annotations
from ast import Str
import dataclasses
from typing import (
    Any,
    Callable,
    Mapping,
    TypedDict,
    TYPE_CHECKING,
    Union,
    Dict,
    TypeVar,
    Generic,
)
from desym.helpers.timed_events_manager import TimedEventsManager

from desym.objects.container import Container
from desym.objects.conveyor.core import Conveyor
from . import events
from . import states

if TYPE_CHECKING:
    import desym.objects.system

import desym.controllers.results_controller
import desym.controllers.behavior_controller
import desym.core


class StopperDescription(TypedDict):
    destiny: list[Stopper.StopperId]
    steps: list[int]
    move_behaviour: list[str]
    rest_steps: list[int]
    default_locked: bool
    priority: int


BehaviorControllerType = TypeVar(
    "BehaviorControllerType",
    bound=desym.controllers.behavior_controller.BaseBehaviourController,
)
ResultsControllerType = TypeVar(
    "ResultsControllerType",
    bound=desym.controllers.results_controller.BaseResultsController,
)


class Stopper(Generic[BehaviorControllerType, ResultsControllerType]):
    StopperId = Union[str, str]

    def __init__(
        self,
        id: str,
        description: StopperDescription,
        simulation: desym.core.Simulation,
        external_function: Callable[..., Any],
        debug,
    ):
        self.id = id
        self.description = description

        # External function to emit events to extenal system
        self.external_function: Callable[..., Any] = external_function

        # Globals
        self.simulation: desym.core.Simulation = simulation
        self.events_manager: TimedEventsManager = self.simulation.events_manager

        self.behaviorInfo = BehaviorInfo(
            id,
            self.description,
            self.simulation.description,
        )

        self.output_conveyors: list[Conveyor] = []
        self.input_conveyors: list[Conveyor] = []

        # Container storage pointer
        self.container: Container | None = None

        # Request time
        self.input_step = 0

        # Stopper composition objects
        self.input_events: events.InputEvents = events.InputEvents(self)
        self.output_events: events.OutputEvents = events.OutputEvents(self)
        self.states: states.StateController = states.StateController(self)

    def __str__(self) -> str:
        return f"Stopper {self.id}"

    def set_input_conveyors(self, input_conveyor: Conveyor) -> None:
        if input_conveyor not in self.input_conveyors:
            self.input_conveyors.append(input_conveyor)

    def set_output_conveyors(self, output_conveyor: Conveyor) -> None:
        if output_conveyor not in self.output_conveyors:
            self.output_conveyors.append(output_conveyor)


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
        self.input_stoppers_ids: list[Stopper.StopperId] = []
        for external_stopper_id, stopper_info in simulation_description.items():
            if stopper_id in stopper_info["destiny"]:
                self.input_stoppers_ids += [external_stopper_id]
