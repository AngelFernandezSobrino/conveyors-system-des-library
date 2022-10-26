from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, TypedDict, Dict, List
from copy import deepcopy

from simulator.objects import Product, Stopper
from simulator.objects.product import ProductType

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
    def __init__(self, product_models):
        super().__init__()

        self.product_models = product_models
        self.production: Dict[str, int] = {}
        self.production_history: Dict[str, List[List[int]]] = {}

    def produce(self, product: Product, actual_time: int):
        self.production[product.model] += 1
        self.production_history[product.model].append([actual_time, self.production[product.model]])
        # self.production_history[product.model]['time'].append(actual_time)
        # self.production_history[product.model]['value'].append(self.production[product.model])

    def simulation_start(self, simulation, actual_time: int):
        for model in self.product_models:
            self.production[model] = 0
            self.production_history[model] = [[0, 0]]
            self.production_history[model].append([actual_time, self.production[model]])
            # self.production_history[model] = {}
            # self.production_history[model]['time'] = [0]
            # self.production_history[model]['value'] = [0]

    def simulation_end(self, simulation, actual_time: int):
        for model in self.product_models:
            self.production_history[model].append([actual_time, self.production[model]])
            # self.production_history[model]['time'].append(actual_time)
            # self.production_history[model]['value'].append(self.production[model])


class TimesResultsController(BaseResultsController):
    def __init__(self, system_description: simulator.objects.system.SystemDescription):
        super().__init__()
        self.time_vector: List[int] = []
        self.times: Dict[str, StopperTimeResults] = {}
        self.previous_stoppers: Dict[str, PreviousData] = {}
        self.busyness: List[list] = [[0, 0]]
        self.system_description = system_description
        self.stopper_history: Dict[str, Dict[str, List[list]]] = {}

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

    def simulation_start(self, simulation, actual_time: int):
        self.simulation_end(simulation, actual_time)

    def simulation_end(self, simulation, actual_time: int):
        self.update_all_times(simulation, actual_time)
        self.time_vector = list(range(0, actual_time))

    def calculate_busyness(self, simulation, actual_time: int):

        if self.busyness[-1][0] != actual_time:
            i = 0
            for stopper_other in simulation.values():

                if stopper_other.request:
                    i += 1
                else:
                    for move in stopper_other.move.values():
                        if move:
                            i += 1
                            break
                # print(stopper_other.stopper_id, stopper_other.request, stopper_other.move, i)
            # print([actual_time, i / len(simulation)])
            self.busyness.append([actual_time, i / len(simulation)])

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
