from timed_events_manager import TimedEventsManager
from tray import Tray
from typing import TypedDict, Dict, List


class StopperInfo(TypedDict):
    id: str
    destiny: list[int]
    steps: list[int]
    behaviour: list[str]
    rest_steps: list[int]


class Stopper:

    def __init__(self, stopper_id: int, topology: list[StopperInfo],
                 simulation: dict, events_register: TimedEventsManager, debug):
        self.debug = debug

        self.stopper_id = stopper_id
        self.simulation = simulation
        self.topology = topology[stopper_id]

        self.output_ids = topology[stopper_id]['destiny']

        self.steps = {
            self.output_ids[k]: v
            for k, v in enumerate(self.topology['steps'])
        }
        self.rest_steps = {
            self.output_ids[k]: v
            for k, v in enumerate(self.topology['rest_steps'])
        }
        self.behaviour = {
            self.output_ids[k]: v
            for k, v in enumerate(self.topology['behaviour'])
        }

        self.events_register = events_register

        self.rest = True
        self.request = False
        self.move = {v: False for v in self.topology['destiny']}
        self.stop = {v: False for v in self.topology['destiny']}

        self.output_trays = {v: False for v in self.topology['destiny']}

        self.input_tray = False
        self.input_ids = []
        for stopper_info in topology:
            if stopper_id in stopper_info['destiny']:
                self.input_ids += [stopper_info['id']]

    def check_request(self):
        if not self.request:
            return
        for destiny in self.output_ids:
            if self.simulation[destiny].check_availability(
            ) and not self.move[destiny] and not self.stop[destiny]:
                self.start_move(destiny)
                return

    def input(self, tray: Tray):
        self.input_tray = tray
        self.rest = False
        self.request = True
        self.check_request()

    def start_move(self, destiny):
        self.request = False
        self.move[destiny] = True
        self.output_trays[destiny] = self.input_tray
        self.input_tray = False
        print(self.stopper_id, destiny)
        self.events_register.push(self.end_move, {'destiny': destiny}, self.steps[destiny])
        if self.behaviour == 'fast':
            self.events_register.push(self.return_rest, {},
                                      self.rest_steps[destiny])

    def return_rest(self):
        self.rest = True
        self.propagate_backwards()

    def propagate_backwards(self):
        for origin in self.input_ids:
            self.simulation[origin].check_request()

    def check_availability(self):
        for origin in self.input_ids:
            if self.simulation[origin].get_move_to(self.stopper_id):
                return False
        if not self.rest:
            return False
        return True

    def get_move_to(self, destiny):
        return self.move[destiny]

    def end_move(self, args):
        self.move[args['destiny']] = False
        self.simulation[args['destiny']].input(self.output_trays[args['destiny']])
        self.output_trays[args['destiny']] = False
        if self.behaviour != 'fast':
            self.return_rest()

    def lock(self, output_id):
        self.stop[output_id] = True
        self.check_request()

    def unlock(self, output_id):
        self.stop[output_id] = False
        self.check_request()


if __name__ == '__main__':

    events_manager = TimedEventsManager()

    simulation_example = {}

    topology_example: list[StopperInfo] = [{
        'id': 0,
        'destiny': [1],
        'steps': [8],
        'behaviour': ['fast'],
        'rest_steps': [1]
    }, {
        'id': 1,
        'destiny': [2],
        'steps': [8],
        'behaviour': ['fast'],
        'rest_steps': [1]
    }, {
        'id': 2,
        'destiny': [3],
        'steps': [8],
        'behaviour': ['fast'],
        'rest_steps': [1]
    }, {
        'id': 3,
        'destiny': [0],
        'steps': [8],
        'behaviour': ['fast'],
        'rest_steps': [1]
    }]

    for i in range(0, 4):
        simulation_example[i] = Stopper(i, topology_example, simulation_example, events_manager)
        print(i)
        print(simulation_example[i])

    simulation_example[0].input(Tray(23, 2))

    for i in range(0, 200):
        events_manager.run()
