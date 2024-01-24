from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Hashable,
    Iterable,
    Optional,
    TypeVar,
    TypedDict,
    Dict,
    List,
)

from enum import Enum
from copy import deepcopy


if TYPE_CHECKING:
    from desym.core import Simulation
    from desym.objects.stopper.core import Stopper
    import desym.objects.system


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

    def simulation_start(self, simulation, step: int):
        pass

    def status_change(self, stopper: Stopper, step: int):
        pass

    def simulation_end(self, simulation, step: int):
        pass


class CounterResultsController(BaseResultsController):
    def __init__(
        self,
        counters: Any,
        data_change_callback: Optional[
            Callable[[CounterResultsController, Any, int], None]
        ] = None,
    ):
        super().__init__()
        self.data_change_callback = data_change_callback
        self.counter_indexes = counters
        self.counters: Dict[Any, int] = {}
        self.counters_timeseries: Dict[Any, List[List[int]]] = {}
        for counter_index in self.counter_indexes:
            self.counters[counter_index] = 0
            self.counters_timeseries[counter_index] = [[0, 0]]

    def increment(self, counter_index: Any, step: int):
        self.counters[counter_index] += 1
        self._register(counter_index, step)

    def simulation_start(self, simulation, step: int):
        for counter_index in self.counter_indexes:
            self.counters_timeseries[counter_index].append(
                [step, self.counters[counter_index]]
            )
            if self.data_change_callback:
                self.data_change_callback(self, counter_index, step)

    def simulation_end(self, simulation, step: int):
        for model in self.counter_indexes:
            self.counters_timeseries[model].append([step, self.counters[model]])

    def _register(self, counter_index: Hashable, step: int):
        self.counters_timeseries[counter_index].append(
            [step, self.counters[counter_index]]
        )
        if self.data_change_callback:
            self.data_change_callback(self, counter_index, step)


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

        self.accumulated_times: Dict[str, StopperTimeResults] = {}
        self.previous_stoppers: Dict[Stopper.StopperId, PreviousData] = {}
        self.busyness: List[list] = [[0, 0]]
        self.system_description = system_description
        self.stopper_history: Dict[str, Dict[str, List[list]]] = {}

        for stopper_id, stopper_description in system_description.items():
            self.accumulated_times[stopper_id] = {"rest": 0, "request": 0, "move": {}}
            self.accumulated_times[stopper_id]["move"] = {
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

    def status_change(self, stopper: Stopper, step: int):
        self.update_times(stopper, step)

    def simulation_start(self, simulation, actual_time: int):
        self.simulation_end(simulation, actual_time)

    def simulation_end(self, simulation, actual_time: int):
        self.update_all_times(simulation, actual_time)

    def calculate_busyness(self, simulation: Simulation, step: int):
        if self.busyness[-1][0] != step:
            i = 0
            for stopper_other in simulation.stoppers.values():
                if stopper_other.states.request:
                    i += 1
                else:
                    for move in stopper_other.states.move.values():
                        if move:
                            i += 1
                            break

            self.busyness.append([step, i / len(simulation.stoppers)])
            if self.busyness_update_callback:
                self.busyness_update_callback(self, i / len(simulation.stoppers), step)
            if self.time_update_callback:
                self.time_update_callback(self, step)

    def update_times(self, stopper: Stopper, step: int):
        if self.previous_stoppers[stopper.id]["state"]["rest"]:
            self.accumulated_times[stopper.id]["rest"] += (
                step - self.previous_stoppers[stopper.id]["time"]
            )

        if self.previous_stoppers[stopper.id]["state"]["request"]:
            self.accumulated_times[stopper.id]["request"] += (
                step - self.previous_stoppers[stopper.id]["time"]
            )

        for destiny in stopper.behaviorInfo.output_stoppers_ids:
            if self.previous_stoppers[stopper.id]["state"]["move"][destiny]:
                self.accumulated_times[stopper.id]["move"][destiny] += (
                    step - self.previous_stoppers[stopper.id]["time"]
                )

        self.previous_stoppers[stopper.id]["state"]["rest"] = deepcopy(
            stopper.states.available
        )
        self.previous_stoppers[stopper.id]["state"]["request"] = deepcopy(
            stopper.states.request
        )
        self.previous_stoppers[stopper.id]["state"]["move"] = deepcopy(
            stopper.states.move
        )
        self.previous_stoppers[stopper.id]["time"] = step
        if self.time_update_callback:
            self.time_update_callback(self, step)

    def update_all_times(self, simulation, actual_time: int):
        for stopper_id in self.system_description.keys():
            self.update_times(simulation[stopper_id], actual_time)
