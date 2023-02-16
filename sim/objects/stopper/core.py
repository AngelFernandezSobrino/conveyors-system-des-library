from __future__ import annotations
from typing import TypedDict, TYPE_CHECKING, Union, Dict

from sim.helpers.timed_events_manager import TimedEventsManager
from sim.objects.tray import Tray
from . import events
from . import states

if TYPE_CHECKING:
    import sim.objects.system

import sim.controllers.results_controller
import sim.controllers.behaviour_controller

StopperId = str


class StopperInfo(TypedDict):
    destiny: list[StopperId]
    steps: list[int]
    move_behaviour: list[str]
    rest_steps: list[int]
    default_locked: bool
    priority: int


class Stopper:
    def __init__(
        self,
        stopper_id: str,
        simulation_description: sim.objects.system.SystemDescription,
        simulation: sim.objects.system.SimulationData,
        events_register: TimedEventsManager,
        behaviour_controllers: Dict[
            str, sim.controllers.behaviour_controller.BaseBehaviourController
        ],
        results_controllers: Dict[
            str, sim.controllers.results_controller.BaseResultsController
        ],
        debug,
    ):
        # Id of the stopper
        self.stopper_id = stopper_id

        # Stopper description data
        self.stopper_description = simulation_description[stopper_id]

        # Controllers pointers
        self.behaviour_controllers = behaviour_controllers
        self.results_controllers = results_controllers

        # Simulation objects pointers
        self.simulation = simulation
        self.events_register = events_register

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
        self.input_stoppers_ids = []
        for external_stopper_id, stopper_info in simulation_description.items():
            if self.stopper_id in stopper_info["destiny"]:
                self.input_stoppers_ids += [external_stopper_id]

        # Stopper tray data
        self.output_items: dict[StopperId, Union[Tray, bool]] = {
            v: False for v in self.stopper_description["destiny"]
        }
        self.input_item: Union[Tray, bool] = False

        # Request time
        self.tray_arrival_time = 0

        # External functions behaviour
        self.return_rest_function = False

        for behaviour_controller in behaviour_controllers.values():
            if self.stopper_id in behaviour_controller.return_rest_functions:
                self.return_rest_function = behaviour_controller.return_rest_functions[
                    self.stopper_id
                ]

        # Stopper composition objects
        self.input_events = events.InputEvents(self)
        self.output_events = events.OutputEvents(self)
        self.states = states.State(self)

    def post_init(self):
        pass

    def check_request(self, *args):
        if not self.states.request:
            return

        for behaviour_controller in self.behaviour_controllers.values():
            behaviour_controller.check_request(
                self.stopper_id,
                {
                    "simulation": self.simulation,
                    "events_register": self.events_register,
                    "stopper": self,
                },
            )
        for destiny in self.output_stoppers_ids:
            if (
                self.check_destiny_available(destiny)
                and not self.move[destiny]
                and not self.management_stop[destiny]
            ):
                self.start_move(destiny)
                return

    def check_destiny_available(self, destiny) -> bool:
        for relative in self.destiny_not_available_v2[destiny].values():
            if relative:
                return False
        return True

    def process_return_rest(self):
        if self.return_rest_function:
            self.return_rest_function(
                {
                    "simulation": self.simulation,
                    "events_register": self.events_register,
                    "stopper_id": self.stopper_id,
                }
            )

    # Results helpers functions
    def state_change(self):
        for results_controller in self.results_controllers.values():
            results_controller.status_change(self, self.events_register.step)
