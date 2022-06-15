from simulator.controllers import results_controller
from simulator import objects


class AccumulatedFinalResultsController(results_controller.BaseResultsController):
    def __init__(self, system_description: objects.system.SystemDescription):
        self.production: dict[str, int] = {}
        self.times: dict[str, results_controller.StopperTimeResults] = {}
        self.previous_stoppers: dict[str, results_controller.PreviousData] = {}
        self.system_description = system_description

        for stopper_id, stopper_description in system_description.items():
            self.times[stopper_id] = {'rest': 0, 'request': 0, 'move': {}}
            self.times[stopper_id]['move'] = {v: 0 for v in stopper_description['destiny']}
            self.previous_stoppers[stopper_id] = {}
            self.previous_stoppers[stopper_id]['state'] = {
                'rest': False,
                'request': False,
                'move': {v: False for v in stopper_description['destiny']}}
            self.previous_stoppers[stopper_id]['time'] = 0

    def status_change(self, stopper: objects.Stopper, actual_time: int):
        results_controller.update_times(self, stopper, actual_time)

    def simulation_end(self, simulation, actual_time: int):
        pass
