from __future__ import annotations

from threading import Thread
from typing import TypedDict, TYPE_CHECKING
import time

from simulator.helpers.timed_events_manager import TimedEventsManager
from simulator.objects.stopper import Stopper

if TYPE_CHECKING:
    import simulator.objects.system
    import simulator.controllers.results_controller.BaseResultsController
    import simulator.controllers.behaviour_controller.BaseBehaviourController


class SimulationConfig(TypedDict):
    real_time_mode: bool
    real_time_step: float
    steps: int


class Core:

    def __init__(self, system_description: simulator.objects.system.SystemDescription, behaviour_controllers: list[
        simulator.controllers.behaviour_controller.BaseBehaviourController], results_controllers: list[
        simulator.controllers.results_controller.BaseResultsController]) -> None:

        self.simulation_config = {'real_time_mode': False, 'real_time_step': 0, 'steps': 0}

        self.system_description = system_description
        self.run_flag = False

        self.end_callback = None

        self.simulation_data = {}
        self.events_manager = TimedEventsManager()
        self.results_controllers = results_controllers

        self.thread = Thread(target=self.thread_function)

        for stopper_id, stopper_description in system_description.items():
            self.simulation_data[stopper_id] = Stopper(stopper_id, system_description, self.simulation_data,
                                                       self.events_manager, behaviour_controllers, results_controllers, False)

        for stopper in self.simulation_data.values():
            stopper.post_init()

        for behaviour_controller in behaviour_controllers:
            for step, external_function in behaviour_controller.external_functions.items():
                self.events_manager.add(external_function, {'simulation': self.simulation_data}, step)

    def sync_status(self, status):
        raise Exception('Method not implemented')

    def run_steps(self, steps: int):
        self.set_config({'real_time_mode': False, 'real_time_step': 0, 'steps': steps})

    def run_real_time_steps(self, steps: int, real_time_step: float):
        self.set_config({'real_time_mode': True, 'real_time_step': real_time_step, 'steps': steps})

    def run_real_time(self, real_time_step: float):
        self.set_config({'real_time_mode': True, 'real_time_step': real_time_step, 'steps': 0})

    def set_config(self, simulation_config: SimulationConfig) -> None:
        self.simulation_config = simulation_config

    def stop(self) -> None:
        self.run_flag = False

    def start(self) -> None:
        if not self.thread.is_alive():
            self.run_flag = True
            self.thread.start()

        else:
            raise Exception('Thread is already running')

    def thread_function(self) -> None:
        if self.simulation_config['real_time_mode']:
            self.sim_thead_real_time()
        else:
            self.sim_thread()

    def sim_thead_real_time(self):
        for results_controller in self.results_controllers:
            results_controller.simulation_end(self.simulation_data, self.events_manager.step)
        start_time = time.time()
        while self.run_flag and (self.simulation_config['steps'] == 0 or self.events_manager.step < self.simulation_config['steps']):
            self.events_manager.run()
            time.sleep(self.simulation_config['real_time_step'] - ((time.time() - start_time) % self.simulation_config['real_time_step']))
        for results_controller in self.results_controllers:
            results_controller.simulation_end(self.simulation_data, self.events_manager.step)

    def sim_thread(self):
        for results_controller in self.results_controllers:
            results_controller.simulation_end(self.simulation_data, self.events_manager.step)
        while self.run_flag and self.events_manager.step < self.simulation_config['steps']:
            self.events_manager.run()
        for results_controller in self.results_controllers:
            results_controller.simulation_end(self.simulation_data, self.events_manager.step)


if __name__ == '__main__':
    from simulator.helpers.test_utils import system_description_example

    core = Core(system_description_example)
    core.set_config({'real_time_mode': False, 'real_time_step': 0, 'steps': 10})
    core.start()
    time.sleep(1)
    core.stop()
