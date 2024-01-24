import copy
from enum import Enum
from typing import TYPE_CHECKING, Dict

from attr import dataclass

from desym.objects.stopper import StopperId


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
    sends: Dict[StopperId, Send]
    destinies: Dict[StopperId, Destiny]
    control: Dict[StopperId, Control]


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
                        actual_state.destinies[destinyId] = States.Destiny.NOT_AVAILABLE
                        actual_state.sends[destinyId] = States.Send.ONGOING
                        self.go_state(actual_state)
            case States(States.Node.SENDING, sends, destinies):
                for destinyId, send in destinies.items():
                    if send == States.Send.ONGOING:
                        actual_state.node = States.Node.SENDING
                        actual_state.sends[destinyId] = States.Send.DELAY
                        self.go_state(actual_state)

                    if send == States.Send.DELAY:
                        actual_state.node = States.Node.REST
                        actual_state.sends[destinyId] = States.Send.NOTHING
                        self.go_state(actual_state)
