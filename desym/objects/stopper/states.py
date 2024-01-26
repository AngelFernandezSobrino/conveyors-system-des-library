from __future__ import annotations
import copy
from enum import Enum
import re
from typing import TYPE_CHECKING, Dict

from attr import dataclass


if TYPE_CHECKING:
    from desym.objects.stopper import StopperId
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
        return f"States(node={self.node.name}, sends={self.sends}, destinies={self.destinies}"


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

    def go_state(self, state: States) -> None:
        prev_state = self.state
        self.state = state

        # if self.c.debug:
        # print(
        #     f"--------------------\n{self.c} State change:\n{prev_state}\n{self.state}"
        # )
        # if self.c.id != "DIR04":
        #     print(f"{self.c} State change")

        self.c.output_events.end_state(prev_state)

        if self.c.external_events_controller is not None:
            self.c.external_events_controller.external_function(self.c)

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
