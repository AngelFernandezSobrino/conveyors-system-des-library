from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from typing import TYPE_CHECKING, Any
from desym.events_manager import CustomEventListener


if TYPE_CHECKING:
    from desym.objects.stopper import states
    from . import core
    from .core import Conveyor

DestinyId = str

# Stopper states class, implement the stopper state machine
## States:
# Available: The stopper is available to receive trays
# Reserved: The stopper is reserved to receive a tray
# Request: The stopper has a tray and is waiting for a destiny to be available
# Move: The stopper is moving a tray to a destiny


@dataclass
class States:
    class S(Enum):
        AVAILABLE = 1
        NOT_AVAILABLE_BY_DESTINY = 2
        NOT_AVAILABLE_BY_MOVING = 3
        MOVING = 4
        NOT_AVAILABLE = 5

    state: S


class State:
    def __init__(self, core: core.Conveyor) -> None:
        self.c = core

        self.state: States = States(States.S.AVAILABLE)

    def go_state(self, context: Any, state: States) -> None:
        prev_state = self.state
        self.state = state

        # if self.c.debug:
        #     print(
        #         f"--------------------\n{self.c} State change:\n{prev_state}\n{self.state}"
        #     )

        self.c.output_events.end_state(prev_state)

        match self.state:
            case States(States.S.MOVING):
                self.c.events_manager.push(
                    CustomEventListener(
                        self.c.states.go_state, (States(States.S.NOT_AVAILABLE),), {}
                    ),
                    self.c.steps,
                )
            case States(States.S.NOT_AVAILABLE_BY_DESTINY):
                self.go_state(None, state=States(States.S.NOT_AVAILABLE))
