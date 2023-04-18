from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict, Dict, List

from enum import Enum
from copy import deepcopy



if TYPE_CHECKING:
    from desym.core import Simulation
    from desym.objects import Item, Stopper
    import desym.objects.system
    from desym.objects.stopper.core import StopperId


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


class CounterResultsController(BaseResultsController):
    def __init__(self, counters: List[str], data_change_callback=None):
        super().__init__()
        self.data_change_callback = data_change_callback
        self.counter_indexes = counters
        self.counters: Dict[str, int] = {}
        self.counters_timeseries: Dict[str, List[List[int]]] = {}

    def increment(self, counter_index: str, actual_time: int):
        self.counters[counter_index] += 1
        self._register(counter_index, actual_time)

    def simulation_start(self, simulation, actual_time: int):
        for model in self.counter_indexes:
            self.counters[model] = 0
            self.counters_timeseries[model] = [[0, 0]]
            self.counters_timeseries[model].append([actual_time, self.counters[model]])
            self.data_change_callback(self, model, actual_time)

    def simulation_end(self, simulation, actual_time: int):
        for model in self.counter_indexes:
            self.counters_timeseries[model].append([actual_time, self.counters[model]])

    def _register(self, counter_index: str, actual_time: int):
        self.counters_timeseries[counter_index].append(
            [actual_time, self.counters[counter_index]]
        )
        if self.data_change_callback:
            self.data_change_callback(self, counter_index, actual_time)


class TimesResultsController(BaseResultsController):
    def __init__(
        self,
        system_description: desym.objects.system.SystemDescription,
        time_update_callback=None,
        busyness_update_callback=None,
    ):
        super().__init__()
        self.time_update_callback = time_update_callback
        self.busyness_update_callback = busyness_update_callback

        self.time_vector: List[int] = []
        self.times: Dict[str, StopperTimeResults] = {}
        self.previous_stoppers: Dict[StopperId, PreviousData] = {}
        self.busyness: List[list] = [[0, 0]]
        self.system_description = system_description
        self.stopper_history: Dict[str, Dict[str, List[list]]] = {}

        for stopper_id, stopper_description in system_description.items():
            self.times[stopper_id] = {"rest": 0, "request": 0, "move": {}}
            self.times[stopper_id]["move"] = {
                v: 0 for v in stopper_description["destiny"]
            }
            self.previous_stoppers[stopper_id] = {
                "state": {
                    "rest": False,
                    "request": False,
                    "move": {v: False for v in stopper_description["destiny"]},
                },
                "time": 0,
            }

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

            self.busyness.append([actual_time, i / len(simulation.stoppers)])
            if self.busyness_update_callback:
                self.busyness_update_callback(self, i / len(simulation.stoppers))
            if self.time_update_callback:
                self.time_update_callback(self)

    def update_times(self, stopper: Stopper, actual_time: int):
        if self.previous_stoppers[stopper.stopper_id]["state"]["rest"]:
            self.times[stopper.stopper_id]["rest"] += (
                actual_time - self.previous_stoppers[stopper.stopper_id]["time"]
            )

        if self.previous_stoppers[stopper.stopper_id]["state"]["request"]:
            self.times[stopper.stopper_id]["request"] += (
                actual_time - self.previous_stoppers[stopper.stopper_id]["time"]
            )

        for destiny in stopper.behaviorInfo.output_stoppers_ids:
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
        if self.time_update_callback:
            self.time_update_callback(self)

    def update_all_times(self, simulation, actual_time: int):
        for stopper_id in self.system_description.keys():
            self.update_times(simulation[stopper_id], actual_time)
