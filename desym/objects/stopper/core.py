from __future__ import annotations
from typing import TypedDict, TYPE_CHECKING, Union, Dict, TypeVar, Generic

from desym.objects.tray import Tray
from . import events
from . import states

if TYPE_CHECKING:
    import desym.objects.system

import desym.controllers.results_controller
import desym.controllers.behaviour_controller
import desym.core

StopperId = str


class StopperDescription(TypedDict):
    destiny: list[StopperId]
    steps: list[int]
    move_behaviour: list[str]
    rest_steps: list[int]
    default_locked: bool
    priority: int


BehaviourControllerType = TypeVar(
    "BehaviourControllerType",
    bound=desym.controllers.behaviour_controller.BaseBehaviourController,
)
ResultsControllerType = TypeVar(
    "ResultsControllerType",
    bound=desym.controllers.results_controller.BaseResultsController,
)


class Stopper(Generic[BehaviourControllerType, ResultsControllerType]):
    def __init__(
        self,
        stopper_id: str,
        stopper_description: StopperDescription,
        simulation_description: desym.objects.system.SystemDescription,
        simulation: desym.core.Simulation,
        behaviour_controllers: Dict[
            str, BehaviourControllerType
        ],
        results_controllers: Dict[
            str, ResultsControllerType
        ],
        debug,
    ):
        # Id of the stopper
        self.stopper_id = stopper_id

        # Stopper description data
        self.stopper_description = stopper_description

        # Controllers pointers
        self.behaviour_controllers = behaviour_controllers
        self.results_controllers = results_controllers

        # Simulation objects pointers
        self.simulation = simulation
        self.events_manager = self.simulation.events_manager

        # Simulation description data
        self.simulation_description = simulation_description

        # Debug mode
        self.debug = debug

        # Stopper behaviour data
        self.default_stopped = self.stopper_description["default_locked"]
        self.output_stoppers_ids = self.stopper_description["destiny"]
        self.move_steps = {
            self.output_stoppers_ids[k]: v
            for k, v in enumerate(self.stopper_description["steps"])
        }
        self.return_available_steps = {
            self.output_stoppers_ids[k]: v
            for k, v in enumerate(self.stopper_description["rest_steps"])
        }
        self.move_behaviour = {
            self.output_stoppers_ids[k]: v
            for k, v in enumerate(self.stopper_description["move_behaviour"])
        }
        self.input_stoppers_ids: list[StopperId] = []
        for external_stopper_id, stopper_info in simulation_description.items():
            if self.stopper_id in stopper_info["destiny"]:
                self.input_stoppers_ids += [external_stopper_id]

        # Stopper tray data
        self.output_trays: dict[StopperId, Union[Tray, None]] = {
            v: None for v in self.stopper_description["destiny"]
        }
        self.input_tray: Union[Tray, None] = None

        # Request time
        self.tray_arrival_time = 0

        # External functions behaviour
        self.return_rest_functions: list[
            desym.controllers.behaviour_controller.ParametrizedFunction
        ] = []
        self.check_requests_functions: list[
            desym.controllers.behaviour_controller.ParametrizedFunction
        ] = []

        for behaviour_controller in behaviour_controllers.values():
            if self.stopper_id in behaviour_controller.return_rest_functions:
                self.return_rest_functions = behaviour_controller.return_rest_functions[
                    self.stopper_id
                ]

            if self.stopper_id in behaviour_controller.check_request_functions:
                self.check_requests_functions = (
                    behaviour_controller.check_request_functions[self.stopper_id]
                )

        # Stopper composition objects
        self.input_events = events.InputEvents(self)
        self.output_events = events.OutputEvents(self)
        self.states = states.State(self)

    def __str__(self) -> str:
        return f"Stopper {self.stopper_id}"

    def post_init(self):
        pass

    def _check_request(self):
        if not self.states.request:
            return

        for behaviour_controller in self.check_requests_functions:
            behaviour_controller(self)

        for destiny in self.output_stoppers_ids:
            if self._check_available_destiny(destiny):
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
