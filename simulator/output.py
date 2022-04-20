from copy import deepcopy

from .product import Product
from .stopper import Stopper, SystemDescription


class ResumeData:
    def __init__(self, system_description: SystemDescription):
        self.production = {}
        self.times = {}
        self.previous_stoppers = {}

        for stopper_id, stopper_description in system_description.items():
            self.times[stopper_id] = {'rest': 0, 'request': 0, 'move': {}}
            self.times[stopper_id]['move'] = {v: 0 for v in stopper_description['destiny']}
            self.previous_stoppers[stopper_id] = {
                'time': 0,
                'rest': True,
                'request': False,
                'move': {v: False for v in stopper_description['destiny']}}

    def produce(self, product: Product):
        self.production[product.model] += 1

    def update_times(self, stopper: Stopper, actual_time: int):
        elapsed_time = actual_time - self.previous_stoppers[stopper.stopper_id]['previous_time']

        if self.previous_stoppers[stopper.stopper_id]['rest']:
            self.times[stopper.stopper_id]['rest'] += elapsed_time

        if self.previous_stoppers[stopper.stopper_id]['request']:
            self.times[stopper.stopper_id]['request'] += elapsed_time

        for destiny in stopper.output_ids:
            if self.previous_stoppers[stopper.stopper_id]['move'][destiny]:
                self.times[stopper.stopper_id]['move'][destiny] += elapsed_time

        self.previous_stoppers[stopper.stopper_id]['previous_time'] = actual_time

        self.previous_stoppers[stopper.stopper_id]['rest'] = deepcopy(stopper.rest)
        self.previous_stoppers[stopper.stopper_id]['request'] = deepcopy(stopper.request)
        self.previous_stoppers[stopper.stopper_id]['move'] = deepcopy(stopper.move)
