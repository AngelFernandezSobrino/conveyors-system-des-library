from threading import Thread, Event
from typing import TypedDict
import time

from .timed_events_manager import TimedEventsManager
from .stopper import Stopper, SystemDescription


class SimulationConfig(TypedDict):
    real_time_mode: bool
    real_time_step: float
    steps: int


class Core:

    def __init__(self, system_description: SystemDescription, controller) -> None:

        self.simulation_config = {'real_time_mode': False, 'real_time_step': 0, 'steps': 0}

        self.system_description = system_description
        self.run_flag = False

        self.end_callback = None

        self.simulation_data = {}
        self.events_manager = TimedEventsManager()

        self.thread = Thread(target=self.run_thread)

        for stopper_id, stopper_description in system_description.items():
            self.simulation_data[stopper_id] = Stopper(stopper_id, system_description, self.simulation_data,
                                                       self.events_manager, controller, False)

    def set_end_callback(self, callback: callable) -> None:
        self.end_callback = callback

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

    def run_thread(self) -> None:
        if self.simulation_config['real_time_mode']:
            self.sim_thead_real_time()
        else:
            self.sim_thread()

    def sim_thead_real_time(self):
        start_time = time.time()
        while self.run_flag and (self.simulation_config['steps'] == 0 or self.events_manager.step < self.simulation_config['steps']):
            self.events_manager.run()
            print(self.events_manager.step)
            time.sleep(self.simulation_config['real_time_step'] - ((time.time() - start_time) % self.simulation_config['real_time_step']))

        self.end_callback()

    def sim_thread(self):
        while self.run_flag and self.events_manager.step < self.simulation_config['steps']:
            self.events_manager.run()
            print(self.events_manager.step)

        self.end_callback()


if __name__ == '__main__':
    from test_utils import system_description_example

    core = Core(system_description_example)
    core.set_config({'real_time_mode': False, 'real_time_step': 0, 'steps': 10})
    core.start()
    time.sleep(1)
    core.stop()
