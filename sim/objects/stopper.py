from __future__ import annotations

from typing import TypedDict, TYPE_CHECKING, Union, Dict

from sim.helpers.timed_events_manager import TimedEventsManager
from .tray import Tray

if TYPE_CHECKING:
    import sim.objects.system
    import sim.controllers.results_controller
    import sim.controllers.behaviour_controller


class StopperInfo(TypedDict):
    destiny: list[str]
    steps: list[int]
    move_behaviour: list[str]
    rest_steps: list[int]
    default_locked: bool
    priority: int


class Stopper:

    def __init__(self, stopper_id: str, simulation_description: sim.objects.system.SystemDescription,
                 simulation: sim.objects.system.SimulationData, events_register: TimedEventsManager,
                 behaviour_controllers: Dict[str, sim.controllers.behaviour_controller.BaseBehaviourController],
                 results_controllers: Dict[str, sim.controllers.results_controller.BaseResultsController], debug):

        # Id of the stopper
        self.stopper_id = stopper_id
        # Stopper description data
        self.description = simulation_description[stopper_id]

        # Controllers pointers
        self.behaviour_controllers = behaviour_controllers
        self.results_controllers = results_controllers

        # Simulation objects pointers
        self.simulation = simulation
        self.events_register = events_register

        # Simulation description data
        self.simulation_description = simulation_description

        # Debug mode
        self.debug = debug

        # Stopper behaviour data
        self.default_locked = self.description['default_locked']
        self.output_ids = self.description['destiny']
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

        # Stopper state machine
        self.rest = True
        self.request = False
        self.move = {v: False for v in self.description['destiny']}

        # Stopper stop flags
        self.management_stop = {v: True if self.description['default_locked'] == 'True' else False for v in
                                self.description['destiny']}
        self.simulation_stop: dict[str, dict[str, bool]] = {}
        self.stopper_relations: dict[str, list[str]] = {}

        for destiny in self.output_ids:
            self.stopper_relations[destiny] = []

        self.output_object = {v: False for v in self.description['destiny']}
        self.input_object: Union[Tray, bool] = False

        self.return_rest_function = False
        for behaviour_controller in behaviour_controllers.values():
            if self.stopper_id in behaviour_controller.return_rest_functions:
                self.return_rest_function = behaviour_controller.return_rest_functions[self.stopper_id]

        self.input_ids = []
        for external_stopper_id, stopper_info in simulation_description.items():
            if self.stopper_id in stopper_info['destiny']:
                self.input_ids += [external_stopper_id]

    def post_init(self):
        self.simulation_stop = {v: {v: False} for v in self.description['destiny']}

        for destiny_id, destiny_stops in self.simulation_stop.items():
            for stopper in self.simulation.values():
                if destiny_id in stopper.output_ids and stopper != self:
                    destiny_stops[stopper.stopper_id] = False

        for destiny_id in self.output_ids:
            for stopper in self.simulation.values():
                if destiny_id in stopper.output_ids and stopper != self:
                    self.stopper_relations[destiny_id] += [stopper.stopper_id]

    def in_event_input_tray(self, tray: Tray):
        self.input_object = tray
        self.rest = False
        self.request = True
        self.request_time = self.events_register.step
        self.status_change()
        self.out_lock_origin()
        self.check_request()

    def transition_check_request(self, *args):
        if not self.request:
            return
        for behaviour_controller in self.behaviour_controllers.values():
            behaviour_controller.check_request(self.stopper_id,
                                               {'simulation': self.simulation, 'events_register': self.events_register,
                                                'stopper': self})
        for destiny in self.output_ids:
            if self.check_destiny_available(destiny) and not self.move[destiny] and not self.management_stop[destiny]:
                self.start_move(destiny)
                return

    def transition_start_move(self, destiny):
        self.request = False
        self.move[destiny] = True
        self.output_object[destiny] = self.input_object
        self.input_object = False
        self.status_change()
        self.events_register.push(self.out_end_move, {'destiny': destiny}, self.steps[destiny])
        if self.default_locked == 1:
            self.in_event_lock(self.output_ids)
        if self.move_behaviour[destiny] == 1:
            self.events_register.push(self.return_rest, {}, self.rest_steps[destiny])
        if self.move_behaviour[destiny] == 0:
            self.return_rest()

    def return_rest(self, *args):
        self.rest = True
        self.status_change()
        if self.return_rest_function:
            self.return_rest_function(
                {'simulation': self.simulation, 'events_register': self.events_register, 'stopper_id': self.stopper_id})
        self.out_unlock_origin()

    def out_end_move(self, args):
        self.move[args['destiny']] = False
        self.out_output(args['destiny'])

        if self.move_behaviour == 3:
            self.return_rest()
        else:
            self.status_change()
            if self.request:
                self.check_request()

    def out_output(self, destiny):
        output_object = self.output_object[destiny]
        self.output_object[destiny] = False
        self.simulation[destiny].in_event_input_tray(output_object)

    def check_destiny_available(self, destiny) -> bool:
        for relative in self.simulation_stop[destiny].values():
            if relative:
                return False
        return True

    def in_event_lock(self, output_ids: list[str]):
        for output_id in output_ids:
            self.management_stop[output_id] = True

    def in_event_unlock(self, output_ids: list[str]):
        for output_id in output_ids:
            self.management_stop[output_id] = False

    def in_relation_lock(self, output_id, relative):
        self.simulation_stop[output_id][relative] = True
        self.check_request()

    def in_relation_unlock(self, output_id, relative):
        self.simulation_stop[output_id][relative] = False
        self.check_request()

    def out_lock_origin(self):
        for origin in self.input_ids:
            self.simulation[origin].in_relation_lock(self.stopper_id, self.stopper_id)

    def out_unlock_origin(self):
        for origin in self.input_ids:
            self.simulation[origin].in_relation_unlock(self.stopper_id, self.stopper_id)
        pass

    def out_lock_relation(self, destiny):
        for relative_stopper in self.stopper_relations[destiny]:
            self.simulation[relative_stopper].in_relation_lock(destiny, self.stopper_id)

    def out_unlock_relation(self, destiny):
        for relative_stopper in self.stopper_relations[destiny]:
            self.simulation[relative_stopper].in_relation_unlock(destiny, self.stopper_id)

    # Results helpers functions
    def status_change(self):
        for results_controller in self.results_controllers.values():
            results_controller.status_change(self, self.events_register.step)