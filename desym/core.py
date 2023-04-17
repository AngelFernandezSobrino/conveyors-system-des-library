from __future__ import annotations
from typing import Callable, Dict, TypedDict, TYPE_CHECKING, TypeVar, Generic, List

import time

from desym.helpers.timed_events_manager import Event, TimedEventsManager
from desym.objects.stopper.core import Stopper, StopperId
from desym.objects.tray import Tray

if TYPE_CHECKING:
    import desym.objects.system

import desym.controllers.results_controller
import desym.controllers.behaviour_controller

import logging

logger = logging.getLogger('desym.core')
logFormatter = logging.Formatter(fmt='%(name)s: %(message)s')
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


class SimulationConfig(TypedDict):
    real_time_mode: bool
    real_time_step: float
    steps: int

BehaviourControllerType = TypeVar("BehaviourControllerType", bound=desym.controllers.behaviour_controller.BaseBehaviourController)
ResultsControllerType = TypeVar("ResultsControllerType", bound=desym.controllers.results_controller.BaseResultsController)

class Simulation(Generic[BehaviourControllerType, ResultsControllerType]):
    def __init__(
        self,
        system_description: desym.objects.system.SystemDescription,
        behaviour_controllers: Dict[
            str, BehaviourControllerType
        ],
        results_controllers: Dict[
            str, ResultsControllerType
        ],
        step_callback: Callable[[int], None] | None,
    ) -> None:
        self.simulation_config = {
            "real_time_mode": False,
            "real_time_step": 0,
            "steps": 0,
        }
        
        self.step_callback = step_callback

        self.simulation = self
        self.system_description = system_description
        self.run_flag = False

        self.end_callback = None

        self.stoppers: dict[StopperId, Stopper[BehaviourControllerType, ResultsControllerType]] = {}
        self.trays: list[Tray] = []

        self.events_manager = TimedEventsManager()
        self.results_controllers = results_controllers

        for stopper_id, stopper_description in self.system_description.items():
            self.stoppers[stopper_id] = Stopper[BehaviourControllerType, ResultsControllerType](
                stopper_id,
                stopper_description,
                self.system_description,
                self,
                behaviour_controllers,
                results_controllers,
                False,
            )

        for stopper in self.stoppers.values():
            stopper.post_init()

        for behaviour_controller in behaviour_controllers.values():
            for (
                step,
                external_function_list,
            ) in behaviour_controller.external_functions.items():
                for external_function in external_function_list:
                    
                    self.events_manager.add(
                        Event(
                            external_function, (self,), {}
                        ),
                        step,
                    )

    def config_steps(self, steps: int):
        self.set_config({"real_time_mode": False, "real_time_step": 0, "steps": steps})

    def config_real_time_steps(self, steps: int, real_time_step: float):
        self.set_config(
            {"real_time_mode": True, "real_time_step": real_time_step, "steps": steps}
        )

    def config_real_time(self, real_time_step: float):
        self.set_config(
            {"real_time_mode": True, "real_time_step": real_time_step, "steps": 0}
        )

    def set_config(self, simulation_config: SimulationConfig) -> None:
        self.simulation_config = simulation_config

    def sim_runner_real_time(self):
        for results_controller in self.results_controllers.values():
            results_controller.simulation_end(self.stoppers, self.events_manager.step)

        start_time = time.time()
        while self.run_flag and (
            self.simulation_config["steps"] == 0
            or self.events_manager.step < self.simulation_config["steps"]
        ):
            self.events_manager.run()
            time.sleep(
                self.simulation_config["real_time_step"]
                - (
                    (time.time() - start_time)
                    % self.simulation_config["real_time_step"]
                )
            )
        for results_controller in self.results_controllers.values():
            results_controller.simulation_end(self.stoppers, self.events_manager.step)

    def sim_runner(self):
        self.run_flag = True
        for results_controller in self.results_controllers.values():
            results_controller.simulation_start(self.stoppers, self.events_manager.step)
        logger.info(f'Run flag: {self.run_flag}')
        logger.info(f'Steps: {self.simulation_config["steps"]}')
        logger.info(f'Events manager step: {self.events_manager.step}')
        while (
            self.run_flag and self.events_manager.step < self.simulation_config["steps"]
        ):
            self.events_manager.run()
            self.step_callback(self)
            # if not (self.events_manager.step % 1000): print(f'Simulation step already processed: {self.events_manager.step}')

        for results_controller in self.results_controllers.values():
            results_controller.simulation_end(self.stoppers, self.events_manager.step)


if __name__ == "__main__":
    from desym.helpers.test_utils import system_description_example

    core = Simulation(system_description_example)
    core.set_config({"real_time_mode": False, "real_time_step": 0, "steps": 10})
    core.sim_runner()