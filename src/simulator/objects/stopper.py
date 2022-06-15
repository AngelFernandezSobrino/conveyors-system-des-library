from __future__ import annotations

from typing import TypedDict, TYPE_CHECKING, Union

from simulator.helpers.timed_events_manager import TimedEventsManager
from .tray import Tray

if TYPE_CHECKING:
    import simulator.objects.system
    import simulator.controllers.results_controller
    import simulator.controllers.behaviour_controller


class StopperInfo(TypedDict):
    destiny: list[str]
    steps: list[int]
    move_behaviour: list[str]
    rest_steps: list[int]
    default_locked: bool
    priority: int


class Stopper:

    def __init__(self, stopper_id: str, simulation_description: simulator.objects.system.SystemDescription,
                 simulation: simulator.objects.system.SimulationData, events_register: TimedEventsManager,
                 behaviour_controllers: list[simulator.controllers.behaviour_controller.BaseBehaviourController],
                 results_controllers: list[simulator.controllers.results_controller.BaseResultsController], debug):

        self.stopper_id = stopper_id
        self.description = simulation_description[stopper_id]

        self.behaviour_controllers = behaviour_controllers
        self.results_controllers = results_controllers
        self.simulation = simulation
        self.events_register = events_register
        self.simulation_description = simulation_description

        self.debug = debug
        self.default_locked = self.description['default_locked']
        self.destiny = self.description['destiny']
        self.steps = {
            self.output_ids[k]: v
            for k, v in enumerate(self.description['steps'])
        }
        self.rest_steps = {
            self.output_ids[k]: v
            for k, v in enumerate(self.description['rest_steps'])
        }
        self.move_behaviour = {
            self.output_ids[k]: v
            for k, v in enumerate(self.description['move_behaviour'])
        }
        self.output_ids = self.description['destiny']

        self.request_time = 0
        self.rest = True
        self.request = False
        self.move = {v: False for v in self.description['destiny']}
        self.external_stop = {v: True if self.description['default_locked'] == 'True' else False for v in
                              self.description['destiny']}
        self.internal_stop: dict[str, dict[str, bool]] = {}

        self.output_trays = {v: False for v in self.description['destiny']}
        self.input_tray: Union[Tray, bool] = False

        self.return_rest_function = False
        for behaviour_controller in behaviour_controllers:
            if self.stopper_id in behaviour_controller.return_rest_functions:
                self.return_rest_function = behaviour_controller.return_rest_functions[self.stopper_id]

        self.input_ids = []
        for external_stopper_id, stopper_info in simulation_description.items():
            if self.stopper_id in stopper_info['destiny']:
                self.input_ids += [external_stopper_id]

    def post_init(self):
        self.internal_stop = {v: { v: False } for v in self.description['destiny']}

        for destiny_id, destiny_stops in self.internal_stop.items():
            for stopper in self.simulation.values():
                if destiny_id in stopper.output_ids:
                    destiny_stops += { stopper.stopper_id: False }

    def check_request(self, *args):
        for behaviour_controller in self.behaviour_controllers:
            behaviour_controller.check_request(self.stopper_id,
                                               {'simulation': self.simulation, 'events_register': self.events_register,
                                                'stopper': self})
        if not self.request:
            return
        for destiny in self.output_ids:
            if self.simulation[destiny].check_availability(exclude_id=self.stopper_id) and not self.move[
                destiny] and not self.stop[destiny]:
                self.start_move(destiny)
                return

    def input(self, tray: Tray):
        self.input_tray = tray
        self.rest = False
        self.request = True
        self.request_time = self.events_register.step
        for results_controller in self.results_controllers:
            results_controller.status_change(self, self.events_register.step)

    def start_move(self, destiny):
        self.request = False
        self.move[destiny] = True
        self.output_trays[destiny] = self.input_tray
        self.input_tray = False
        for results_controller in self.results_controllers:
            results_controller.status_change(self, self.events_register.step)
        self.events_register.push(self.end_move, {'destiny': destiny}, self.steps[destiny])
        if self.default_locked == 1:
            self.lock(destiny)
        if self.move_behaviour[destiny] == 1:
            self.events_register.push(self.return_rest_and_propagate, {}, self.rest_steps[destiny])
        if self.move_behaviour[destiny] == 0:
            self.return_rest_and_propagate()

    def return_rest_and_propagate(self, *args):
        self.rest = True
        for results_controller in self.results_controllers:
            results_controller.status_change(self, self.events_register.step)
        if self.return_rest_function:
            self.return_rest_function(
                {'simulation': self.simulation, 'events_register': self.events_register, 'stopper_id': self.stopper_id})
        self.propagate_backwards()

    def return_rest(self, *args):
        self.rest = True
        for results_controller in self.results_controllers:
            results_controller.status_change(self, self.events_register.step)
        if self.return_rest_function:
            self.return_rest_function(
                {'simulation': self.simulation, 'events_register': self.events_register, 'stopper_id': self.stopper_id})

    def propagate_backwards(self):
        if self.description['priority'] == 0:
            for origin in self.input_ids:
                self.simulation[origin].check_request()
        else:
            for origin in reversed(self.input_ids):
                self.simulation[origin].check_request()

    def check_availability(self, exclude_id=None):
        for origin in self.input_ids:
            if origin == exclude_id:
                pass
            else:
                if self.simulation[origin].get_move_to(self.stopper_id):
                    return False
        if self.rest:
            return True
        return False

    def get_move_to(self, destiny):
        return self.move[destiny]

    def end_move(self, args):
        self.move[args['destiny']] = False
        self.simulation[args['destiny']].input(self.output_trays[args['destiny']])
        self.output_trays[args['destiny']] = False
        if self.move_behaviour == 3:
            self.return_rest()
            for results_controller in self.results_controllers:
                results_controller.status_change(self, self.events_register.step)
            self.propagate_backwards()
        else:
            for results_controller in self.results_controllers:
                results_controller.status_change(self, self.events_register.step)
            self.check_request()
        self.simulation[args['destiny']].check_request()

    def lock(self, output_id):
        self.stop[output_id] = True

    def unlock(self, output_id):
        self.stop[output_id] = False
        self.check_request()


if __name__ == '__main__':

    events_manager = TimedEventsManager()

    simulation_data_example = {}

    controller = simulator.controllers.behaviour_controller.BaseBehaviourController()

    from src.simulator.helpers.test_utils import system_description_example

    for stopper_id, stopper_description in system_description_example.items():
        simulation_data_example[stopper_id] = Stopper(stopper_id, system_description_example, simulation_data_example,
                                                      events_manager, controller, False)
        print(stopper_id)
        print(simulation_data_example[stopper_id])

    simulation_data_example['0'].input(Tray(23, 2))

    for i in range(0, 20000):
        print(i)
        events_manager.run()
