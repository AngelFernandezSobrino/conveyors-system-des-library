from __future__ import annotations
import dataclasses
from typing import Mapping, TypedDict, TYPE_CHECKING, Union, Dict, TypeVar, Generic

from desym.objects.tray import Tray
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
        stopper_id: str,
        stopper_description: StopperDescription,
        simulation_description: desym.objects.system.SystemDescription,
        simulation: desym.core.Simulation,
        behavior_controllers: Mapping[str, BehaviorControllerType],
        results_controllers: Mapping[str, ResultsControllerType],
        debug,
    ):
        self.stopper_id = stopper_id
        self.stopper_description = stopper_description
        self.behaviour_controllers = behavior_controllers
        self.results_controllers = results_controllers
        self.simulation_description = simulation_description

        # Global pointers
        self.simulation = simulation
        self.events_manager = self.simulation.events_manager

        self.behaviorInfo = BehaviorInfo(
            stopper_id,
            stopper_description,
            simulation_description,
        )

        self.output_stoppers: list[Stopper] = []
        self.input_stoppers: list[Stopper] = []

        # Stopper tray data
        self.output_trays: dict[Stopper.StopperId, Union[Tray, None]] = {
            v: None for v in self.stopper_description["destiny"]
        }
        self.input_tray: Union[Tray, None] = None

        # Request time
        self.tray_arrival_time = 0

        # External functions behavior
        self.return_rest_functions: list[
            desym.controllers.behavior_controller.ParametrizedFunction
        ] = []
        self.check_requests_functions: list[
            desym.controllers.behavior_controller.ParametrizedFunction
        ] = []

        for behavior_controller in behavior_controllers.values():
            if self.stopper_id in behavior_controller.return_rest_functions:
                self.return_rest_functions = behavior_controller.return_rest_functions[
                    self.stopper_id
                ]

            if self.stopper_id in behavior_controller.check_request_functions:
                self.check_requests_functions = (
                    behavior_controller.check_request_functions[self.stopper_id]
                )

        # Stopper composition objects
        self.input_events = events.InputEvents(self)
        self.output_events = events.OutputEvents(self)
        self.states = states.State(self)

    def __str__(self) -> str:
        return f"Stopper {self.stopper_id}"

    def post_init(self):
        for output_stopper_id in self.behaviorInfo.output_stoppers_ids:
            if not len(self.output_stoppers):
                self.output_stoppers = [self.simulation.stoppers[output_stopper_id]]
            else:
                self.output_stoppers += [self.simulation.stoppers[output_stopper_id]]

        for input_stopper_id in self.behaviorInfo.input_stoppers_ids:
            if not len(self.input_stoppers):
                self.input_stoppers = [self.simulation.stoppers[input_stopper_id]]
            else:
                self.input_stoppers += [self.simulation.stoppers[input_stopper_id]]

    def _check_request(self):
        if not self.states.request:
            return

        for behavior_controller in self.check_requests_functions:
            behavior_controller(self)

        self._check_move()

    def _check_move(self):
        if not self.states.request:
            return
        for destiny in self.behaviorInfo.output_stoppers_ids:
            if not self.states.management_stop[
                destiny
            ] and self._check_available_destiny(destiny):
                self.states.go_move(destiny)
                return

    def its_available(self) -> bool:
        return self.states.available

    def _check_available_destiny(self, destiny):
        return self.simulation.stoppers[destiny].its_available()

    def _process_return_rest(self):
        for return_rest_function in self.return_rest_functions:
            return_rest_function(self)

    # Results helpers functions
    def _state_change(self):
        for results_controller in self.results_controllers.values():
            results_controller.status_change(self, self.events_manager.step)


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
