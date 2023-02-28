from __future__ import annotations
from typing import Dict, TypedDict, TYPE_CHECKING

import time

from sim.helpers.timed_events_manager import Event, TimedEventsManager
from sim.objects.stopper.core import Stopper

if TYPE_CHECKING:
    import sim.objects.system

import sim.controllers.results_controller
import sim.controllers.behaviour_controller


class SimulationConfig(TypedDict):
    real_time_mode: bool
    real_time_step: float
    steps: int


class Simulation:
    def __init__(
        self,
        system_description: sim.objects.system.SystemDescription,
        behaviour_controllers: Dict[
            str, sim.controllers.behaviour_controller.BaseBehaviourController
        ],
        results_controllers: Dict[
            str, sim.controllers.results_controller.BaseResultsController
        ],
    ) -> None:
        self.simulation_config = {
            "real_time_mode": False,
            "real_time_step": 0,
            "steps": 0,
        }

        self.system_description = system_description
        self.run_flag = False

        self.end_callback = None

        self.stoppers = {}
        self.events_manager = TimedEventsManager()
        self.results_controllers = results_controllers

        for stopper_id, stopper_description in self.system_description.items():
            self.stoppers[stopper_id] = Stopper(
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
                external_function,
            ) in behaviour_controller.external_functions.items():
                print('Add external function ' + str(external_function) + ' at step ' + str(step))
                self.events_manager.add(
                    Event(external_function, ({"simulation": self.stoppers},), {}), step
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
            results_controller.simulation_end(
                self.stoppers, self.events_manager.step
            )

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
        for results_controller in self.results_controllers:
            results_controller.simulation_end(
                self.stoppers, self.events_manager.step
            )

    def sim_runner(self):
        self.run_flag = True
        for results_controller in self.results_controllers.values():
            results_controller.simulation_start(
                self.stoppers, self.events_manager.step
            )
        print('Run flag: ' + str(self.run_flag))
        print('Steps: ' + str(self.simulation_config["steps"]))
        print('Events manager step: ' + str(self.events_manager.step))
        while (
            self.run_flag and self.events_manager.step < self.simulation_config["steps"]
        ):
            self.events_manager.run()   
            print(self.events_manager.step)

        for results_controller in self.results_controllers.values():
            results_controller.simulation_end(
                self.stoppers, self.events_manager.step
            )


if __name__ == "__main__":
    from sim.helpers.test_utils import system_description_example

    core = Simulation(system_description_example)
    core.set_config({"real_time_mode": False, "real_time_step": 0, "steps": 10})
    core.sim_runner()
