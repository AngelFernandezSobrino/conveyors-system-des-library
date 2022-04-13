from typing import Dict

from timed_events_manager import TimedEventsManager

from stopper import StopperInfo, Stopper, SystemDescription
from tray import Tray


class Core:

    def __init__(self, system_description: SystemDescription) -> None:

        self.system_description = system_description

        self.stop = False

        self.simulation_data = {}
        self.events_manager = TimedEventsManager()

        for stopper_id, stopper_description in system_description.items():
            self.simulation_data[stopper_id] = Stopper(stopper_id, system_description, self.simulation_data,
                                                       self.events_manager, False)

    def run_for_steps(self, steps: int) -> None:
        for i in range(0, steps):
            self.events_manager.run()

    def run_until_stopped(self, stop) -> None:
        self.stop = stop
        while not stop:
            self.events_manager.run()


if __name__ == '__main__':
    from test_utils import system_description_example

    core = Core(system_description_example)

    core.run_for_steps(200)
