from __future__ import annotations
import copy
import logging
from enum import Enum
from typing import TYPE_CHECKING, Dict

from attr import dataclass

from desim.custom_logging import (
    get_logger,
    LOGGER_BASE_NAME,
    LOGGER_NAME_PADDING,
    LOGGER_STATE_CHANGE_COLOR,
    LOGGER_STATE_GROUP_NAME,
    LOGGER_STOPPER_COLOR,
    LOGGER_STOPPER_NAME,
)

if TYPE_CHECKING:
    from desim.objects.stopper import StopperId
    from . import core

@dataclass
class StateModel:
    class Node(Enum):
        REST = 0
        RESERVED = 1
        OCCUPIED = 2
        SENDING = 3

        def __str__(self) -> str:
            return self.name

        def __repr__(self) -> str:
            return self.name

    class Send(Enum):
        NOTHING = 0
        ONGOING = 1
        DELAY = 2
        SENT = 3

        def __str__(self) -> str:
            return str(self.value)

        def __repr__(self) -> str:
            return self.name

    class Destiny(Enum):
        AVAILABLE = 0
        NOT_AVAILABLE = 1

        def __str__(self) -> str:
            return str(self.value)

        def __repr__(self) -> str:
            return self.name

    class Control(Enum):
        LOCKED = 0
        UNLOCKED = 1

    node: Node
    sends: Dict[StopperId, Send]
    destinies: Dict[StopperId, Destiny]
    control: Dict[StopperId, Control]

    def __str__(self) -> str:
        return f"States(node={self.node.name}, sends={self.sends}, destinies={self.destinies}, control={self.control})"

@dataclass
class StateModelChange:

    node: StateModel.Node = None
    sends: Dict[StopperId, StateModel.Send] = None
    destinies: Dict[StopperId, StateModel.Destiny] = None
    control: Dict[StopperId, StateModel.Control] = None

def simplified_string(self: StateModel | StateModelChange) -> str:
    result = ""
    if self.node is not None:
        result += f" {self.node.name} "
    if self.sends is not None:
        result += f"sends {self.sends} "
    if self.destinies is not None:
        result += f"destinies {self.destinies} "
    if self.control is not None:
        result += f"control {self.control}"
    return result

class StateController:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

        self.state: StateModel = StateModel(
            StateModel.Node.REST,
            {
                destinyId: StateModel.Send.NOTHING
                for destinyId in self.c.description["destiny"]
            },
            {
                destinyId: StateModel.Destiny.AVAILABLE
                for destinyId in self.c.description["destiny"]
            },
            {
                destinyId: StateModel.Control.UNLOCKED
                for destinyId in self.c.description["destiny"]
            },
        )

        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_STOPPER_NAME}.{self.c.id}.state",
            f"{LOGGER_STOPPER_COLOR}{LOGGER_BASE_NAME}.{LOGGER_STOPPER_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_STATE_CHANGE_COLOR}{LOGGER_STATE_GROUP_NAME} - ",
        )

        self.state_change_id = 0

    def end_state_node_rest(self):
        self.c.o.not_available()

    def end_state_node_occupied(self):
        for destinyId, send in self.c.s.state.sends.items():
            if send == StateModel.Send.ONGOING:
                self.c.o.reserve(destinyId)
                return

    def end_state_node_sending(self):
        for destiny_id, send in self.state.sends.items():
            if send == StateModel.Send.DELAY:
                self.c.o.send(destiny_id)
                self.state.sends[destiny_id] = StateModel.Send.NOTHING

        self.c.o.available()

    def go_state_control_lock(self, stopper_id: StopperId):
        self.state.control[stopper_id] = StateModel.Control.LOCKED

    def go_state_destiny_not_available(self, stopper_id: StopperId):
        self.state.destinies[stopper_id] = StateModel.Destiny.NOT_AVAILABLE

    def go_state(self, state_changes: StateModelChange, side_effects=True) -> None:

        # if self.logger.level == logging.DEBUG:
        #     self.logger.debug(
        #         f"To {simplified_string(state_changes)}"
        #     )

        prev_state_node = self.state.node

        if state_changes.destinies is not None:
            for destiny_id, destiny_state in state_changes.destinies.items():
                self.state.destinies[destiny_id] = destiny_state

        if state_changes.sends is not None:
            for destiny_id, sends_state in state_changes.sends.items():
                self.state.sends[destiny_id] = sends_state

        if state_changes.control is not None:
            for destiny_id, control_state in state_changes.control.items():
                self.state.control[destiny_id] = control_state

        if state_changes.node is not None:
            self.state.node = state_changes.node

        self.state_change_id += 1
        last_state_change_id = self.state_change_id

        if state_changes.node is not None:
            if (
                    prev_state_node == StateModel.Node.REST
                    and self.state != StateModel.Node.REST
            ):
                self.end_state_node_rest()
            elif (
                    prev_state_node == StateModel.Node.OCCUPIED
                    and self.state != StateModel.Node.OCCUPIED
            ):
                self.end_state_node_occupied()
            elif (
                    prev_state_node == StateModel.Node.SENDING
                    and self.state != StateModel.Node.SENDING
            ):
                self.end_state_node_sending()

        if self.state_change_id != last_state_change_id:
            return

        if self.c.external_events_controller is not None:
            self.c.external_events_controller.external_function(self.c)
            if self.state_change_id != last_state_change_id:
                return

        if self.state.node == StateModel.Node.OCCUPIED:
            for destiny_id, destiny in self.state.destinies.items():
                if destiny == StateModel.Destiny.AVAILABLE and self.state.control[destiny_id] == StateModel.Control.UNLOCKED:
                    self.go_state(StateModelChange(node=StateModel.Node.SENDING, sends={ destiny_id: StateModel.Send.ONGOING }, destinies={destiny_id: StateModel.Destiny.NOT_AVAILABLE}))
                    return

        if self.state.node == StateModel.Node.SENDING:
            for destiny_id, destiny_state in self.state.destinies.items():
                if self.state.sends[destiny_id] == StateModel.Send.ONGOING:
                    self.go_state(StateModelChange(sends={ destiny_id: StateModel.Send.DELAY }))
                    return

                if self.state.sends[destiny_id] == StateModel.Send.DELAY:
                    self.go_state(StateModelChange(node=StateModel.Node.REST))
                    return
