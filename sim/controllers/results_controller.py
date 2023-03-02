from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict, Dict, List

from enum import Enum
from copy import deepcopy


if TYPE_CHECKING:
    from sim.core import Simulation
    from sim.objects import Item, Stopper
    import sim.objects.system


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

    def simulation_start(self, simulation, actual_time: int):
        raise NotImplementedError

    def status_change(self, stopper: Stopper, actual_time: int):
        pass

    def simulation_end(self, simulation, actual_time: int):
        raise NotImplementedError


class CounterController(BaseResultsController):
    def __init__(self, item_types: List[str]):
        super().__init__()

        self.item_types = item_types
        self.counter: Dict[str, int] = {}
        self.counter_history: Dict[str, List[List[int]]] = {}

    def produce(self, Item: Item, actual_time: int):
        self.counter[Item.item_type] += 1
        self.counter_history[Item.item_type].append(
            [actual_time, self.counter[Item.item_type]]
        )
        # self.production_history[product.model]['time'].append(actual_time)
        # self.production_history[product.model]['value'].append(self.production[product.model])

    def simulation_start(self, simulation, actual_time: int):
        for model in self.item_types:
            self.counter[model] = 0
            self.counter_history[model] = [[0, 0]]
            self.counter_history[model].append([actual_time, self.counter[model]])
            # self.production_history[model] = {}
            # self.production_history[model]['time'] = [0]
            # self.production_history[model]['value'] = [0]

    def simulation_end(self, simulation, actual_time: int):
        for model in self.item_types:
            self.counter_history[model].append([actual_time, self.counter[model]])
            # self.production_history[model]['time'].append(actual_time)
            # self.production_history[model]['value'].append(self.production[model])


class TimesController(BaseResultsController):
    def __init__(self, system_description: sim.objects.system.SystemDescription):
        super().__init__()
        self.time_vector: List[int] = []
        self.times: Dict[str, StopperTimeResults] = {}
        self.previous_stoppers: Dict[str, PreviousData] = {}
        self.busyness: List[list] = [[0, 0]]
        self.system_description = system_description
        self.stopper_history: Dict[str, Dict[str, List[list]]] = {}

        for stopper_id, stopper_description in system_description.items():
            self.times[stopper_id] = {"rest": 0, "request": 0, "move": {}}
            self.times[stopper_id]["move"] = {
                v: 0 for v in stopper_description["destiny"]
            }
            self.previous_stoppers[stopper_id] = {}
            self.previous_stoppers[stopper_id]["state"] = {
                "rest": False,
                "request": False,
                "move": {v: False for v in stopper_description["destiny"]},
            }
            self.previous_stoppers[stopper_id]["time"] = 0

    def status_change(self, stopper: Stopper, actual_time: int):
        self.update_times(stopper, actual_time)

    def simulation_start(self, simulation, actual_time: int):
        self.simulation_end(simulation, actual_time)

    def simulation_end(self, simulation, actual_time: int):
        self.update_all_times(simulation, actual_time)
        self.time_vector = list(range(0, actual_time))

    def calculate_busyness(self, simulation: Simulation, actual_time: int):
        if self.busyness[-1][0] != actual_time:
            i = 0
            for stopper_other in simulation.stoppers.values():
                if stopper_other.states.request:
                    i += 1
                else:
                    for move in stopper_other.states.move.values():
                        if move:
                            i += 1
                            break
                # print(stopper_other.stopper_id, stopper_other.request, stopper_other.move, i)
            # print([actual_time, i / len(simulation)])
            self.busyness.append([actual_time, i / len(simulation.stoppers)])

    def update_times(self, stopper: Stopper, actual_time: int):
        if self.previous_stoppers[stopper.stopper_id]["state"]["rest"]:
            self.times[stopper.stopper_id]["rest"] += (
                actual_time - self.previous_stoppers[stopper.stopper_id]["time"]
            )

        if self.previous_stoppers[stopper.stopper_id]["state"]["request"]:
            self.times[stopper.stopper_id]["request"] += (
                actual_time - self.previous_stoppers[stopper.stopper_id]["time"]
            )

        for destiny in stopper.output_stoppers_ids:
            if self.previous_stoppers[stopper.stopper_id]["state"]["move"][destiny]:
                self.times[stopper.stopper_id]["move"][destiny] += (
                    actual_time - self.previous_stoppers[stopper.stopper_id]["time"]
                )

        self.previous_stoppers[stopper.stopper_id]["state"]["rest"] = deepcopy(
            stopper.states.available
        )
        self.previous_stoppers[stopper.stopper_id]["state"]["request"] = deepcopy(
            stopper.states.request
        )
        self.previous_stoppers[stopper.stopper_id]["state"]["move"] = deepcopy(
            stopper.states.move
        )
        self.previous_stoppers[stopper.stopper_id]["time"] = actual_time

    def update_all_times(self, simulation, actual_time: int):
        for stopper_id in self.system_description.keys():
            self.update_times(simulation[stopper_id], actual_time)
