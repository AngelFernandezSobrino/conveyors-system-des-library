import copy
from enum import Enum
from typing import TYPE_CHECKING, List

from attr import dataclass


if TYPE_CHECKING:
    from . import core


@dataclass
class States:
    class Node(Enum):
        REST = 1
        RESERVED = 2
        OCCUPIED = 3
        SENDING = 4

    class Send(Enum):
        NOTHING = 1
        ONGOING = 1
        DELAY = 2

    class Destiny(Enum):
        AVAILABLE = 1
        NOT_AVAILABLE = 2

    class Control(Enum):
        LOCKED = 1
        UNLOCKED = 2

    node: Node
    sends: List[Send]
    destinies: List[Destiny]
    control: List[Control]


class StateController:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

        self.state: States = States(
            States.Node.REST,
            [States.Send.NOTHING for _ in self.c.description["destiny"]],
            [States.Destiny.AVAILABLE for _ in self.c.description["destiny"]],
            [States.Control.UNLOCKED for _ in self.c.description["destiny"]],
        )

    def go_state(self, state: States) -> None:
        prev_state = self.state
        self.state = state
        self.c.output_events.end_state(prev_state)

        if self.c.external_events_controller is not None:
            self.c.external_events_controller.external_function(self.c)

        actual_state = copy.deepcopy(self.state)
        match self.state:
            case States(States.Node.OCCUPIED, sends, destinies):
                for index, destiny in enumerate(destinies):
                    if (
                        destiny == States.Destiny.AVAILABLE
                        and self.state.control[index] == States.Control.UNLOCKED
                    ):
                        actual_state.node = States.Node.SENDING
                        actual_state.destinies[index] = States.Destiny.NOT_AVAILABLE
                        actual_state.sends[index] = States.Send.ONGOING
                        self.go_state(actual_state)
            case States(States.Node.SENDING, sends, destinies):
                for index, send in enumerate(sends):
                    if send == States.Send.ONGOING:
                        actual_state.node = States.Node.SENDING
                        actual_state.sends[index] = States.Send.DELAY
                        self.go_state(actual_state)

                    if send == States.Send.DELAY:
                        actual_state.node = States.Node.REST
                        actual_state.sends[index] = States.Send.NOTHING
                        self.go_state(actual_state)
