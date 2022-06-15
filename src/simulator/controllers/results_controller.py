from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict, Dict
from copy import deepcopy

from simulator.objects import Product, Stopper

if TYPE_CHECKING:
    import simulator.objects.system


class StopperTimeResults(TypedDict):
    rest: int
    request: int
    move: Dict[str, int]


class PreviousData(TypedDict):
    state: PreviousState
    time: int


class PreviousState(TypedDict):
    rest: bool
    request: bool
    move: Dict[str, bool]


class BaseResultsController:
    def __init__(self):
        pass

    def status_change(self, stopper: Stopper, actual_time: int):
        pass

    def simulation_end(self, simulation, actual_time: int):
        pass


class ProductionResultsController(BaseResultsController):
    def __init__(self):
        super().__init__()
        self.production: Dict[str, int] = {}

    def produce(self, product: Product):
        self.production[product.model] += 1


class TimesResultsController(BaseResultsController):
    def __init__(self, system_description: simulator.objects.system.SystemDescription):
        super().__init__()
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
        self.update_times(stopper, actual_time)

    def simulation_end(self, simulation, actual_time: int):
        self.update_all_times(simulation, actual_time)

    def update_times(self, stopper: Stopper, actual_time: int):
        if self.previous_stoppers[stopper.stopper_id]['state']['rest']:
            self.times[stopper.stopper_id]['rest'] += actual_time - self.previous_stoppers[stopper.stopper_id]['time']

        if self.previous_stoppers[stopper.stopper_id]['state']['request']:
            self.times[stopper.stopper_id]['request'] += actual_time - \
                                                         self.previous_stoppers[stopper.stopper_id]['time']

        for destiny in stopper.output_ids:
            if self.previous_stoppers[stopper.stopper_id]['state']['move'][destiny]:
                self.times[stopper.stopper_id]['move'][destiny] += \
                    actual_time - self.previous_stoppers[stopper.stopper_id]['time']

        self.previous_stoppers[stopper.stopper_id]['state']['rest'] = deepcopy(stopper.rest)
        self.previous_stoppers[stopper.stopper_id]['state']['request'] = deepcopy(stopper.request)
        self.previous_stoppers[stopper.stopper_id]['state']['move'] = deepcopy(stopper.move)
        self.previous_stoppers[stopper.stopper_id]['time'] = actual_time

    def update_all_times(self, simulation, actual_time: int):
        for stopper_id in self.system_description.keys():
            self.update_times(simulation[stopper_id], actual_time)
