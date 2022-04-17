from time import sleep

from simulator.config_parser import ConfigParser
from simulator.core import Core, RealTimeConfig


class Api:

    def __init__(self, config_path: str) -> None:
        self.thread = None
        self.config_parser = ConfigParser(config_path)
        self.config_parser.parse('config_parser')
        if self.config_parser.config_available:
            self.simulation_core = Core(self.config_parser.config)
        else:
            raise Exception('Config not available')

    def sync_status(self, status):
        raise Exception('Method not implemented')

    def run_steps(self, steps: int):
        self.simulation_core.set_real_time_config({'real_time_mode': False, 'real_time_step': 0})
        self.thread = self.simulation_core.run_for_steps(steps)

    def run_real_time_steps(self, steps: int, real_time_step: float):
        self.simulation_core.set_real_time_config({'real_time_mode': True, 'real_time_step': real_time_step})
        self.thread = self.simulation_core.run_for_steps(steps)

    def run_real_time(self, real_time_step: float):
        self.simulation_core.set_real_time_config({'real_time_mode': True, 'real_time_step': real_time_step})
        self.thread = self.simulation_core.run_until_stopped()

    def start(self):
        self.simulation_core.start()

    def stop(self):
        self.simulation_core.stop()

    def wait(self):
        self.thread.join()

    def reset(self):
        self.simulation_core = Core(self.config_parser.config)


if __name__ == '__main__':
    from test_utils import system_description_example

    simulation_api = Api('../data/simulator_config.xlsx')

    print('Running simulation...')
    print('Run steps')
    simulation_api.run_steps(10)
    simulation_api.wait()
    simulation_api.reset()
    print('Run real time steps')
    simulation_api.run_real_time_steps(10, 0.1)
    simulation_api.wait()
    simulation_api.reset()
    print('Run real time')
    simulation_api.run_real_time(0.1)
    sleep(1)
    simulation_api.stop()
    simulation_api.reset()
