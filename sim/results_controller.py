from __future__ import annotations
import copy
from turtle import st
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
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

from sympy import Ge

from sim.item import Product


if TYPE_CHECKING:
    from desym.core import Simulation
    import desym.objects.stopper.core

import desym.objects.stopper.states
import desym.objects.conveyor.states


class StopperCounters(desym.objects.stopper.states.States):
    def __init__(self, actual_state: desym.objects.stopper.states.States):
        self.node = copy.deepcopy(actual_state.node)
        self.sends = copy.deepcopy(actual_state.sends)
        self.destinies = copy.deepcopy(actual_state.destinies)
        self.control = copy.deepcopy(actual_state.control)

        self.nodeTimers: Dict[desym.objects.stopper.states.States.Node, int] = {
            desym.objects.stopper.states.States.Node.REST: 0,
            desym.objects.stopper.states.States.Node.RESERVED: 0,
            desym.objects.stopper.states.States.Node.OCCUPIED: 0,
            desym.objects.stopper.states.States.Node.SENDING: 0,
        }

        self.nodeTimersLastUpdate: Dict[
            desym.objects.stopper.states.States.Node, int
        ] = {
            desym.objects.stopper.states.States.Node.REST: 0,
            desym.objects.stopper.states.States.Node.RESERVED: 0,
            desym.objects.stopper.states.States.Node.OCCUPIED: 0,
            desym.objects.stopper.states.States.Node.SENDING: 0,
        }

        self.sendsTimers: Dict[
            desym.objects.stopper.StopperId,
            Dict[desym.objects.stopper.states.States.Send, int],
        ] = {}
        self.sendsTimersLastUpdate: Dict[
            desym.objects.stopper.StopperId,
            Dict[desym.objects.stopper.states.States.Send, int],
        ] = {}

        for destiny_stopper_id in self.sends.keys():
            self.sendsTimers[destiny_stopper_id] = {
                desym.objects.stopper.states.States.Send.NOTHING: 0,
                desym.objects.stopper.states.States.Send.ONGOING: 0,
                desym.objects.stopper.states.States.Send.DELAY: 0,
            }
            self.sendsTimersLastUpdate[destiny_stopper_id] = {
                desym.objects.stopper.states.States.Send.NOTHING: 0,
                desym.objects.stopper.states.States.Send.ONGOING: 0,
                desym.objects.stopper.states.States.Send.DELAY: 0,
            }

        self.destiniesTimers: Dict[
            desym.objects.stopper.StopperId,
            Dict[desym.objects.stopper.states.States.Destiny, int],
        ] = {}
        self.destiniesTimersLastUpdate: Dict[
            desym.objects.stopper.StopperId,
            Dict[desym.objects.stopper.states.States.Destiny, int],
        ] = {}

        for destiny_stopper_id in self.destinies.keys():
            self.destiniesTimers[destiny_stopper_id] = {
                desym.objects.stopper.states.States.Destiny.AVAILABLE: 0,
                desym.objects.stopper.states.States.Destiny.NOT_AVAILABLE: 0,
            }
            self.destiniesTimersLastUpdate[destiny_stopper_id] = {
                desym.objects.stopper.states.States.Destiny.AVAILABLE: 0,
                desym.objects.stopper.states.States.Destiny.NOT_AVAILABLE: 0,
            }

        self.controlTimers: Dict[
            desym.objects.stopper.StopperId,
            Dict[desym.objects.stopper.states.States.Control, int],
        ] = {}
        self.controlTimersLastUpdate: Dict[
            desym.objects.stopper.StopperId,
            Dict[desym.objects.stopper.states.States.Control, int],
        ] = {}

        for destiny_stopper_id in self.control.keys():
            self.controlTimers[destiny_stopper_id] = {
                desym.objects.stopper.states.States.Control.LOCKED: 0,
                desym.objects.stopper.states.States.Control.UNLOCKED: 0,
            }
            self.controlTimersLastUpdate[destiny_stopper_id] = {
                desym.objects.stopper.states.States.Control.LOCKED: 0,
                desym.objects.stopper.states.States.Control.UNLOCKED: 0,
            }


T = TypeVar("T", bound=Iterable)


class CounterController(Generic[T]):
    def __init__(self, counters_indexes: T):
        self.counter_indexes = counters_indexes
        self.counters = {}

        for counter_index in self.counter_indexes:
            self.counters[counter_index] = 0

    def increment(self, counter_index: T):
        self.counters[counter_index] += 1


class CronoController:
    def __init__(
        self,
        simulation: Simulation,
    ):
        self.simulation = simulation

        self.stoppersResults: Dict[
            desym.objects.stopper.StopperId, StopperCounters
        ] = {}

        for stopper_id, stopper in simulation.stoppers.items():
            self.stoppersResults[stopper_id] = StopperCounters(stopper.states.state)

        # for conveyor_id, conveyor in simulation.conveyors.items():
        #     self.previous_conveyor_state[conveyor_id] = copy.deepcopy(conveyor.states.state)

    def update_stopper_times(self, stopper: desym.objects.stopper.core.Stopper):
        if self.stoppersResults[stopper.id].node != stopper.states.state.node:
            self.stoppersResults[stopper.id].nodeTimers[stopper.states.state.node] += (
                self.simulation.timed_events_manager.step
                - self.stoppersResults[stopper.id].nodeTimersLastUpdate[
                    stopper.states.state.node
                ]
            )

        for destiny_stopper_id, send in self.stoppersResults[stopper.id].sends.items():
            if send != stopper.states.state.sends[destiny_stopper_id]:
                self.stoppersResults[stopper.id].sendsTimers[destiny_stopper_id][
                    stopper.states.state.sends[destiny_stopper_id]
                ] += (
                    self.simulation.timed_events_manager.step
                    - self.stoppersResults[stopper.id].sendsTimersLastUpdate[
                        destiny_stopper_id
                    ][stopper.states.state.sends[destiny_stopper_id]]
                )

        for destiny_stopper_id, destiny in self.stoppersResults[
            stopper.id
        ].destinies.items():
            if destiny != stopper.states.state.destinies[destiny_stopper_id]:
                self.stoppersResults[stopper.id].destiniesTimers[destiny_stopper_id][
                    stopper.states.state.destinies[destiny_stopper_id]
                ] += (
                    self.simulation.timed_events_manager.step
                    - self.stoppersResults[stopper.id].destiniesTimersLastUpdate[
                        destiny_stopper_id
                    ][stopper.states.state.destinies[destiny_stopper_id]]
                )

        for destiny_stopper_id, control in self.stoppersResults[
            stopper.id
        ].control.items():
            if control != stopper.states.state.control[destiny_stopper_id]:
                self.stoppersResults[stopper.id].controlTimers[destiny_stopper_id][
                    stopper.states.state.control[destiny_stopper_id]
                ] += (
                    self.simulation.timed_events_manager.step
                    - self.stoppersResults[stopper.id].controlTimersLastUpdate[
                        destiny_stopper_id
                    ][stopper.states.state.control[destiny_stopper_id]]
                )

        self.stoppersResults[stopper.id].node = copy.deepcopy(stopper.states.state.node)
        self.stoppersResults[stopper.id].sends = copy.deepcopy(
            stopper.states.state.sends
        )
        self.stoppersResults[stopper.id].destinies = copy.deepcopy(
            stopper.states.state.destinies
        )
        self.stoppersResults[stopper.id].control = copy.deepcopy(
            stopper.states.state.control
        )

    def update_all_times(self):
        for stopper in self.simulation.stoppers.values():
            self.update_stopper_times(stopper)


def calculate_busyness(simulation: Simulation):
    stoppers_in_rest = 0

    for stopper in simulation.stoppers.values():
        if (
            stopper.states.state.node
            == desym.objects.stopper.states.States.Node.RESERVED
            or stopper.states.state.node
            == desym.objects.stopper.states.States.Node.REST
        ):
            stoppers_in_rest += 1

    return stoppers_in_rest / len(simulation.stoppers)
