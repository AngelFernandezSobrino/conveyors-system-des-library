import threading as th
import multiprocessing as mp
import time

from .core import Core
from .stopper import SystemDescription


class Api:

    def __init__(self, system_description: SystemDescription, controller):
        self.system_description = system_description
        self.controller = controller
        self.core = None
        self.thread1 = None
        self.thread2 = None
        self.end_event = None
        self.queue = mp.Queue()
        self.feedback_event = mp.Event()
        self.pipe_main, self.pipe_process = mp.Pipe()

        self.state = 'stopped'

        self.process = mp.Process(target=self.core_process)
        self.process.start()

    def sync_status(self, status):
        raise Exception('Method not implemented')

    def run_steps(self, steps: int):
        self.pipe_main.send({'sim_config': {'real_time_mode': False, 'real_time_step': 0, 'steps': steps}, 'command': 'run'})

    def run_real_time_steps(self, steps: int, real_time_step: float):
        self.pipe_main.send({'sim_config': {'real_time_mode': True, 'real_time_step': real_time_step, 'steps': steps}, 'command': 'run'})

    def run_real_time(self, real_time_step: float):
        self.pipe_main.send({'sim_config': {'real_time_mode': True, 'real_time_step': real_time_step, 'steps': 0}, 'command': 'run'})

    def stop(self):
        self.pipe_main.send({'command': 'stop'})

    def wait(self):
        self.feedback_event.wait()

    def core_process(self):
        self.config_core()
        try:
            self.thread1.start()
            self.thread2.start()
            self.end_event.wait()
            self.feedback_event.set()
        except KeyboardInterrupt:
            pass
        finally:
            print("Closing Loop")
            self.thread1 = None
            self.thread2 = None

    def config_core(self):
        self.core = Core(self.system_description, self.controller)
        self.core.set_end_callback(self.sim_end)
        self.thread1 = th.Thread(target=self.manager)
        self.thread2 = th.Thread(target=self.daemon)
        self.end_event = th.Event()

    def sim_end(self):
        self.end_event.set()

    def daemon(self):
        self.end_event.wait()
        self.feedback_event.set()

    def manager(self):
        while True:
            msg = self.pipe_process.recv()
            if msg['command'] == 'stop':
                self.core.stop()
            elif msg['command'] == 'run':
                self.core.set_config(msg['sim_config'])
                self.core.start()
            elif msg['command'] == 'reset':
                self.config_core()
            else:
                raise Exception('Unknown command')


if __name__ == '__main__':

    from config_parser import ConfigParser
    simulator_api = None

    config_path = '../data/simulator_config.xlsx'

    config_parser = ConfigParser(config_path)
    config_parser.parse('config_parser')
    if not config_parser.config_available:
        raise Exception('Config not available')
    try:

        simulation_api = Api(config_parser.config)

        print('Running simulation...')
        print('Run steps')
        simulation_api.run_steps(10)
        simulation_api.wait()
        simulation_api = Api(config_parser.config)
        print('Run real time steps')
        simulation_api.run_real_time_steps(10, 0.1)
        simulation_api.wait()
        simulation_api = Api(config_parser.config)
        print('Run real time')
        simulation_api.run_real_time(0.1)
        time.sleep(15)
        simulation_api.stop()

    except KeyboardInterrupt:
        pass
    finally:
        print("Closing Process")
        try:
            simulation_api
        except NameError:
            pass
        else:
            simulation_api.process.terminate()
