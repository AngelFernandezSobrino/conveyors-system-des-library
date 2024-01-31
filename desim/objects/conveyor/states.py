from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import logging

from typing import TYPE_CHECKING, Any
from desim.events_manager import CustomEventListener
from desim.custom_logging import (
    LOGGER_BASE_NAME,
    LOGGER_CONVEYOR_COLOR,
    LOGGER_CONVEYOR_NAME,
    LOGGER_NAME_PADDING,
    LOGGER_STATE_CHANGE_COLOR,
    LOGGER_STATE_GROUP_NAME,
    get_logger,
)


if TYPE_CHECKING:
    from desim.objects.stopper import states
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
        # NOT_AVAILABLE_BY_DESTINY = 2
        NOT_AVAILABLE_BY_MOVING = 3
        MOVING = 4
        NOT_AVAILABLE = 5
        WAITING_RECEIVE = 6

    state: S

    def __str__(self) -> str:
        return f"{self.state.name}"


class State:
    def __init__(self, core: core.Conveyor) -> None:
        self.c = core
        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME}.{self.c.id}.state",
            f"{LOGGER_CONVEYOR_COLOR}{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_STATE_CHANGE_COLOR}{LOGGER_STATE_GROUP_NAME} - ",
        )

        self.state: States = States(States.S.AVAILABLE)
        self.state_change_id = 0

    def go_state(self, context: Any, state: States) -> None:
        if self.c.debug:
            self.logger.debug(f"From {self.state} -> To {state}")
        if state == self.state:
            return

        last_state_change_id = self.state_change_id
        self.state_change_id += 1

        prev_state = self.state
        self.state = state

        self.c.output_events.end_state(prev_state)

        if self.state_change_id != last_state_change_id + 1:
            return

        match self.state:
            case States(States.S.MOVING):
                self.c.events_manager.push(
                    CustomEventListener(
                        self.c.states.go_state, (States(States.S.NOT_AVAILABLE),), {}
                    ),
                    self.c.steps,
                )
                return
            case States(States.S.NOT_AVAILABLE_BY_MOVING):
                self.go_state(None, state=States(States.S.WAITING_RECEIVE))
                return
