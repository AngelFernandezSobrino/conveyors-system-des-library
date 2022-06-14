from simulator import BaseResultsController
from simulator.results_controller import update_times


class AccumulatedFinalResultsController(BaseResultsController):
    def __init__(self, system_description: simulator.objects.system.SystemDescription):
        self.production: Dict[str, int] = {}
        self.times: Dict[str, StopperTimeResults] = {}
        self.previous_stoppers: Dict[str, PreviousData] = {}
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

    def status_change(self, stopper: Stopper, actual_time: int):
        update_times(self, stopper, actual_time)

    def simulation_end(self, simulation, actual_time: int):
        pass
