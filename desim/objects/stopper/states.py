from __future__ import annotations
import copy
from enum import Enum
from typing import TYPE_CHECKING, Dict

from attr import dataclass
from torch import ne


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
class States:
    class Node(Enum):
        REST = 1
        RESERVED = 2
        OCCUPIED = 3
        SENDING = 4

        def __str__(self) -> str:
            return self.name

        def __repr__(self) -> str:
            return self.name

    class Send(Enum):
        NOTHING = 1
        ONGOING = 2
        DELAY = 3

        def __str__(self) -> str:
            return str(self.value)

        def __repr__(self) -> str:
            return self.name

    class Destiny(Enum):
        AVAILABLE = 1
        NOT_AVAILABLE = 2

        def __str__(self) -> str:
            return str(self.value)

        def __repr__(self) -> str:
            return self.name

    class Control(Enum):
        LOCKED = 1
        UNLOCKED = 2

    node: Node
    sends: Dict[StopperId, Send]
    destinies: Dict[StopperId, Destiny]
    control: Dict[StopperId, Control]

    def __str__(self) -> str:
        return f"States(node={self.node.name}, sends={self.sends}, destinies={self.destinies}, control={self.control})"

    def simplified_string(self) -> str:
        result = f"("
        if "node" in self.__dict__:
            result += f"node={self.node.name}, "
        if "sends" in self.__dict__:
            result += f"sends={self.sends}, "
        if "destinies" in self.__dict__:
            result += f"destinies={self.destinies}"
        if "control" in self.__dict__:
            result += f"control={self.control}"
        result += ")"
        return result

    def get_changes(self, other: States) -> str:
        result = []
        if self.node != other.node:
            result.append(f"node={self.node.name} -> {other.node.name}")

        sends = []
        for send in self.sends:
            if self.sends[send] != other.sends[send]:
                sends.append(
                    f"{send}={self.sends[send].name} -> {other.sends[send].name}"
                )

        if len(sends) > 0:
            result.append(f"sends=({', '.join(sends)})")

        destinies = []
        for destiny in self.destinies:
            if self.destinies[destiny] != other.destinies[destiny]:
                destinies.append(
                    f"{destiny}={self.destinies[destiny].name} -> {other.destinies[destiny].name}"
                )

        if len(destinies) > 0:
            result.append(f"destinies=({', '.join(destinies)})")

        controls: list = []
        for control in self.control:
            if self.control[control] != other.control[control]:
                controls.append(
                    f"{controls}={self.control[control].name} -> {other.control[control].name}"
                )

        if len(controls) > 0:
            result.append(f"control=({', '.join(controls)})")

        return ", ".join(result)


class StateController:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

        self.state: States = States(
            States.Node.REST,
            {
                destinyId: States.Send.NOTHING
                for destinyId in self.c.description["destiny"]
            },
            {
                destinyId: States.Destiny.AVAILABLE
                for destinyId in self.c.description["destiny"]
            },
            {
                destinyId: States.Control.UNLOCKED
                for destinyId in self.c.description["destiny"]
            },
        )

        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_STOPPER_NAME}.{self.c.id}.state",
            f"{LOGGER_STOPPER_COLOR}{LOGGER_BASE_NAME}.{LOGGER_STOPPER_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_STATE_CHANGE_COLOR}{LOGGER_STATE_GROUP_NAME} - ",
        )

        self.state_change_id = 0

    def go_state(self, state: States, side_effects=True) -> None:
        prev_state = self.state
        self.state = state

        last_state_change_id = self.state_change_id
        self.state_change_id += 1

        if self.c.debug:
            self.logger.debug(f"{prev_state.get_changes(self.state)}")
            self.logger.debug(f"Prev state: {prev_state}")

        self.c.output_events.end_state(prev_state)

        if self.c.external_events_controller is not None:
            self.c.external_events_controller.external_function(self.c)

        if self.state_change_id != last_state_change_id + 1:
            return

        actual_state = copy.deepcopy(self.state)
        match self.state:
            case States(States.Node.OCCUPIED, sends, destinies):
                for destinyId, destiny in destinies.items():
                    if (
                        destiny == States.Destiny.AVAILABLE
                        and self.state.control[destinyId] == States.Control.UNLOCKED
                    ):
                        actual_state.node = States.Node.SENDING
                        actual_state.sends[destinyId] = States.Send.ONGOING
                        actual_state.destinies[destinyId] = States.Destiny.NOT_AVAILABLE
                        self.go_state(actual_state)
            case States(States.Node.SENDING, sends=sends, destinies=destinies):
                for destiny_id, destiny_state in destinies.items():
                    if sends[destiny_id] == States.Send.ONGOING:
                        actual_state.sends[destiny_id] = States.Send.DELAY
                        self.go_state(actual_state)
                        return

                    if sends[destiny_id] == States.Send.DELAY:
                        actual_state.node = States.Node.REST
                        actual_state.sends[destiny_id] = States.Send.NOTHING
                        self.go_state(actual_state)
                        return
