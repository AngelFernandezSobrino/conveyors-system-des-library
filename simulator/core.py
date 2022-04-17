from multiprocessing import Process, Pipe
from threading import Thread
from typing import TypedDict

import time

from timed_events_manager import TimedEventsManager

from stopper import Stopper, SystemDescription


class RealTimeConfig(TypedDict):
    real_time_mode: bool
    real_time_step: float


def sim_thead_real_time(simulator, pipe: Pipe):
    start_time = time.time()
    while not simulator.stop_flag and (simulator.steps == 0 or simulator.events_manager.step < simulator.steps):
        print('Time step: ' + str(simulator.events_manager.step))
        simulator.events_manager.run()
        time.sleep(simulator.real_time['real_time_step'] - ((time.time() - start_time) % simulator.real_time['real_time_step']))
    pipe.send(simulator.simulation_data)


def sim_thread(simulator, pipe: Pipe):
    while not simulator.stop_flag and (simulator.steps == 0 or simulator.events_manager.step < simulator.steps):
        print('Step: ' + str(simulator.events_manager.step))
        simulator.events_manager.run()
    pipe.send(simulator.simulation_data)


class Core:

    def __init__(self, system_description: SystemDescription) -> None:

        self.real_time = {'real_time_mode': False, 'real_time_step': 0}

        self.system_description = system_description

        self.steps = 0
        self.stop_flag = False

        self.simulation_data = {}
        self.events_manager = TimedEventsManager()

        for stopper_id, stopper_description in system_description.items():
            self.simulation_data[stopper_id] = Stopper(stopper_id, system_description, self.simulation_data,
                                                       self.events_manager, False)

    def set_real_time_config(self, real_time_config: RealTimeConfig) -> None:
        self.real_time = real_time_config

    def start(self) -> None:
        self.stop_flag = False

    def stop(self) -> None:
        self.stop_flag = True

    def run_for_steps(self, steps: int) -> Thread:
        self.start()
        self.steps = steps
        return self.run_thread()

    def run_until_stopped(self) -> Thread:
        self.start()
        self.steps = 0
        return self.run_thread()

    def run_thread(self) -> Thread:
        th = Thread(target=self.run_process)
        th.start()
        return th

    def run_process(self) -> None:
        master_p, child_p = Pipe()
        if self.real_time['real_time_mode']:
            wk = Process(target=sim_thead_real_time, args=(self, child_p))
            wk.start()
        else:
            wk = Process(target=sim_thread, args=(self, child_p))
            wk.start()
        wk.join()
        self.update_from_process(master_p)

    def update_from_process(self, master_p) -> None:
        self.simulation_data = master_p.recv()


if __name__ == '__main__':
    from test_utils import system_description_example

    core = Core(system_description_example)

    core.run_for_steps(200)
