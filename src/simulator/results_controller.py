from __future__ import annotations

from typing import TYPE_CHECKING
from copy import deepcopy

from simulator.objects import Product, Stopper

if TYPE_CHECKING:
    pass


class ResultsController:
    def __init__(self, system_description: src.simulator.objects.system.SystemDescription):
        self.production = {}
        self.times = {}
        self.previous_stoppers = {}

        for stopper_id, stopper_description in system_description.items():
            self.times[stopper_id] = {'rest': 0, 'request': 0, 'move': {}}
            self.times[stopper_id]['move'] = {v: 0 for v in stopper_description['destiny']}
            self.previous_stoppers[stopper_id] = {}
            self.previous_stoppers[stopper_id]['state'] = {
                'rest': False,
                'request': False,
                'move': {v: False for v in stopper_description['destiny']}}
            self.previous_stoppers[stopper_id]['time'] = {
                'rest': 0,
                'request': 0,
                'move': {v: 0 for v in stopper_description['destiny']}}

    def produce(self, product: Product):
        self.production[product.model] += 1

    def update_times(self, stopper: Stopper, actual_time: int):
        print('Stopper Id: ', stopper.stopper_id, ' Actual Time: ', actual_time)
        if self.previous_stoppers[stopper.stopper_id]['state']['rest'] and not stopper.rest:
            self.times[stopper.stopper_id]['rest'] += actual_time - self.previous_stoppers[stopper.stopper_id]['time'][
                'rest']
        if stopper.rest:
            self.previous_stoppers[stopper.stopper_id]['time']['rest'] = actual_time

        if self.previous_stoppers[stopper.stopper_id]['state']['request'] and not stopper.rest:
            self.times[stopper.stopper_id]['request'] += actual_time - \
                                                         self.previous_stoppers[stopper.stopper_id]['time']['request']
        if stopper.request:
            self.previous_stoppers[stopper.stopper_id]['time']['request'] = actual_time

        for destiny in stopper.output_ids:
            if self.previous_stoppers[stopper.stopper_id]['state']['move'][destiny] and not stopper.move[destiny]:
                self.times[stopper.stopper_id]['move'][destiny] += \
                    actual_time - self.previous_stoppers[stopper.stopper_id]['time']['move'][destiny]
            if stopper.move[destiny]:
                self.previous_stoppers[stopper.stopper_id]['time']['move'][destiny] = actual_time

        self.previous_stoppers[stopper.stopper_id]['state']['rest'] = deepcopy(stopper.rest)
        self.previous_stoppers[stopper.stopper_id]['state']['request'] = deepcopy(stopper.request)
        self.previous_stoppers[stopper.stopper_id]['state']['move'] = deepcopy(stopper.move)
