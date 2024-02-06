from __future__ import annotations
import copy
from typing import (
    TYPE_CHECKING,
    Generic,
    Iterable,
    TypeVar,
    Dict,
)

if TYPE_CHECKING:
    from desim.core import Simulation
    import desim.objects.stopper.core

import desim.objects.stopper.states
import desim.objects.conveyor.states

import logging

logger = logging.getLogger("mains.results_controller")
logger.propagate = False
logFormatter = logging.Formatter("\N{ESC}[0m{name: <30s} - {message}", style="{")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)


class StopperCounter(desim.objects.stopper.states.StateModel):
    def __init__(self, actual_state: desim.objects.stopper.states.StateModel):
        self.node = copy.deepcopy(actual_state.node)
        self.sends = copy.deepcopy(actual_state.sends)
        self.destinies = copy.deepcopy(actual_state.destinies)
        self.control = copy.deepcopy(actual_state.control)

        self.nodeTimers: Dict[desim.objects.stopper.states.StateModel.Node, int] = {
            desim.objects.stopper.states.StateModel.Node.REST: 0,
            desim.objects.stopper.states.StateModel.Node.RESERVED: 0,
            desim.objects.stopper.states.StateModel.Node.OCCUPIED: 0,
            desim.objects.stopper.states.StateModel.Node.SENDING: 0,
        }

        self.nodeTimersLastUpdate: Dict[
            desim.objects.stopper.states.StateModel.Node, int
        ] = {
            desim.objects.stopper.states.StateModel.Node.REST: 0,
            desim.objects.stopper.states.StateModel.Node.RESERVED: 0,
            desim.objects.stopper.states.StateModel.Node.OCCUPIED: 0,
            desim.objects.stopper.states.StateModel.Node.SENDING: 0,
        }

        self.sendsTimers: Dict[
            desim.objects.stopper.StopperId,
            Dict[desim.objects.stopper.states.StateModel.Send, int],
        ] = {}
        self.sendsTimersLastUpdate: Dict[
            desim.objects.stopper.StopperId,
            Dict[desim.objects.stopper.states.StateModel.Send, int],
        ] = {}

        for destiny_stopper_id in self.sends.keys():
            self.sendsTimers[destiny_stopper_id] = {
                desim.objects.stopper.states.StateModel.Send.NOTHING: 0,
                desim.objects.stopper.states.StateModel.Send.ONGOING: 0,
                desim.objects.stopper.states.StateModel.Send.DELAY: 0,
            }
            self.sendsTimersLastUpdate[destiny_stopper_id] = {
                desim.objects.stopper.states.StateModel.Send.NOTHING: 0,
                desim.objects.stopper.states.StateModel.Send.ONGOING: 0,
                desim.objects.stopper.states.StateModel.Send.DELAY: 0,
            }

        self.destiniesTimers: Dict[
            desim.objects.stopper.StopperId,
            Dict[desim.objects.stopper.states.StateModel.Destiny, int],
        ] = {}
        self.destiniesTimersLastUpdate: Dict[
            desim.objects.stopper.StopperId,
            Dict[desim.objects.stopper.states.StateModel.Destiny, int],
        ] = {}

        for destiny_stopper_id in self.destinies.keys():
            self.destiniesTimers[destiny_stopper_id] = {
                desim.objects.stopper.states.StateModel.Destiny.AVAILABLE: 0,
                desim.objects.stopper.states.StateModel.Destiny.NOT_AVAILABLE: 0,
            }
            self.destiniesTimersLastUpdate[destiny_stopper_id] = {
                desim.objects.stopper.states.StateModel.Destiny.AVAILABLE: 0,
                desim.objects.stopper.states.StateModel.Destiny.NOT_AVAILABLE: 0,
            }

        self.controlTimers: Dict[
            desim.objects.stopper.StopperId,
            Dict[desim.objects.stopper.states.StateModel.Control, int],
        ] = {}
        self.controlTimersLastUpdate: Dict[
            desim.objects.stopper.StopperId,
            Dict[desim.objects.stopper.states.StateModel.Control, int],
        ] = {}

        for destiny_stopper_id in self.control.keys():
            self.controlTimers[destiny_stopper_id] = {
                desim.objects.stopper.states.StateModel.Control.LOCKED: 0,
                desim.objects.stopper.states.StateModel.Control.UNLOCKED: 0,
            }
            self.controlTimersLastUpdate[destiny_stopper_id] = {
                desim.objects.stopper.states.StateModel.Control.LOCKED: 0,
                desim.objects.stopper.states.StateModel.Control.UNLOCKED: 0,
            }


T = TypeVar("T", bound=Iterable)


class CountersController(Generic[T]):
    def __init__(self, counters_indexes: T):
        self.counter_indexes = counters_indexes
        self.counters = {}

        for counter_index in self.counter_indexes:
            self.counters[counter_index] = 0

    def increment(self, counter_index: T):
        self.counters[counter_index] += 1

    def get(self, counter_index: T):
        return self.counters[counter_index]


class CronoController:
    def __init__(
        self,
        simulation: Simulation,
    ):
        self.simulation = simulation

        self.stoppersResults: Dict[desim.objects.stopper.StopperId, StopperCounter] = {}

        for stopper_id, stopper in simulation.stoppers.items():
            self.stoppersResults[stopper_id] = StopperCounter(stopper.s.state)

        # for conveyor_id, conveyor in simulation.conveyors.items():
        #     self.previous_conveyor_state[conveyor_id] = copy.deepcopy(conveyor.states.state)

    def update_stopper_times(self, stopper: desim.objects.stopper.core.Stopper):
        if self.stoppersResults[stopper.id].node != stopper.s.state.node:
            self.stoppersResults[stopper.id].nodeTimers[stopper.s.state.node] += (
                self.simulation.timed_events_manager.step
                - self.stoppersResults[stopper.id].nodeTimersLastUpdate[
                    stopper.s.state.node
                ]
            )

        for destiny_stopper_id, send in self.stoppersResults[stopper.id].sends.items():
            if send != stopper.s.state.sends[destiny_stopper_id]:
                self.stoppersResults[stopper.id].sendsTimers[destiny_stopper_id][
                    stopper.s.state.sends[destiny_stopper_id]
                ] += (
                    self.simulation.timed_events_manager.step
                    - self.stoppersResults[stopper.id].sendsTimersLastUpdate[
                        destiny_stopper_id
                    ][stopper.s.state.sends[destiny_stopper_id]]
                )

        for destiny_stopper_id, destiny in self.stoppersResults[
            stopper.id
        ].destinies.items():
            if destiny != stopper.s.state.destinies[destiny_stopper_id]:
                self.stoppersResults[stopper.id].destiniesTimers[destiny_stopper_id][
                    stopper.s.state.destinies[destiny_stopper_id]
                ] += (
                    self.simulation.timed_events_manager.step
                    - self.stoppersResults[stopper.id].destiniesTimersLastUpdate[
                        destiny_stopper_id
                    ][stopper.s.state.destinies[destiny_stopper_id]]
                )

        for destiny_stopper_id, control in self.stoppersResults[
            stopper.id
        ].control.items():
            if control != stopper.s.state.control[destiny_stopper_id]:
                self.stoppersResults[stopper.id].controlTimers[destiny_stopper_id][
                    stopper.s.state.control[destiny_stopper_id]
                ] += (
                    self.simulation.timed_events_manager.step
                    - self.stoppersResults[stopper.id].controlTimersLastUpdate[
                        destiny_stopper_id
                    ][stopper.s.state.control[destiny_stopper_id]]
                )

        self.stoppersResults[stopper.id].node = copy.deepcopy(stopper.s.state.node)
        self.stoppersResults[stopper.id].sends = copy.deepcopy(stopper.s.state.sends)
        self.stoppersResults[stopper.id].destinies = copy.deepcopy(
            stopper.s.state.destinies
        )
        self.stoppersResults[stopper.id].control = copy.deepcopy(
            stopper.s.state.control
        )

    def update_all_times(self):
        for stopper in self.simulation.stoppers.values():
            self.update_stopper_times(stopper)


def calculate_ratio_non_rest_stoppers(simulation: Simulation):
    stoppers_in_rest = 0
    logger.debug("Calculating ratio non rest stoppers")
    for stopper in simulation.stoppers.values():

        logger.debug(
            f"Stopper name: {stopper.id} - Stopper state: {stopper.s.state.node}"
        )

        if stopper.s.state.node == desim.objects.stopper.states.StateModel.Node.REST:
            logger.debug(f"Stopper {stopper.id} is in rest")
            stoppers_in_rest += 1

    logger.debug(
        f"Stoppers in rest: {stoppers_in_rest} - Total stoppers: {len(simulation.stoppers)}"
    )
    logger.debug(f"Result: {1 - stoppers_in_rest / len(simulation.stoppers)}")
    return 1 - stoppers_in_rest / len(simulation.stoppers)


def calculate_ratio_moving_conveyors(simulation: Simulation):
    conveyors_in_movement = 0

    logger.debug("Calculating ratio moving conveyors")
    logger.debug(f"Conveyors: {simulation.conveyors}")
    for conveyor in simulation.conveyors.values():
        logger.debug(
            f"Conveyor name: {conveyor.id} - Conveyor state: {conveyor.s.state.state}"
        )
        if (
            conveyor.s.state.state == desim.objects.conveyor.states.StateModel.S.MOVING
            or conveyor.s.state.state
            == desim.objects.conveyor.states.StateModel.S.NOT_AVAILABLE_BY_MOVING
        ):
            logger.debug(f"Conveyor {conveyor.id} is in movement")
            conveyors_in_movement += 1

    logger.debug(
        f"Conveyors in movement: {conveyors_in_movement} - Total conveyors: {len(simulation.conveyors)}"
    )
    logger.debug(f"Result: {conveyors_in_movement / len(simulation.conveyors)}")

    return conveyors_in_movement / len(simulation.conveyors)
