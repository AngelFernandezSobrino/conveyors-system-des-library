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
class StateModel:
    class S(Enum):
        AVAILABLE = 0
        NOT_AVAILABLE_BY_MOVING = 1
        MOVING = 2
        NOT_AVAILABLE = 3
        WAITING_RECEIVE = 4

    state: S

    def __str__(self) -> str:
        return f"{self.state.name}"


class StateController:
    def __init__(self, core: core.Conveyor) -> None:
        self.c = core
        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME}.{self.c.id}.state",
            f"{LOGGER_CONVEYOR_COLOR}{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_STATE_CHANGE_COLOR}{LOGGER_STATE_GROUP_NAME} - ",
        )

        self.state: StateModel = StateModel(StateModel.S.AVAILABLE)
        self.state_change_id = 0

    def go_state(self, context: Any, state: StateModel) -> None:
        # if self.logger.level == logging.DEBUG:
        #     self.logger.debug(f"From {self.state} -> To {state}")

        if state == self.state:
            if self.logger.level == logging.DEBUG:
                self.logger.debug(f"From {self.state} -> To {state}")

            pass
            return

        self.state_change_id += 1
        last_state_change_id = self.state_change_id

        prev_state = self.state
        self.state = state

        self.c.o.end_state(prev_state)

        if self.state_change_id != last_state_change_id:
            return

        match self.state:
            case StateModel(StateModel.S.MOVING):
                self.c.events_manager.push(
                    CustomEventListener(
                        self.c.s.go_state,
                        (StateModel(StateModel.S.NOT_AVAILABLE),),
                        {},
                    ),
                    self.c.steps,
                )
                return
            case StateModel(StateModel.S.NOT_AVAILABLE_BY_MOVING):
                self.go_state(None, state=StateModel(StateModel.S.WAITING_RECEIVE))
                return

    def dump(self):
        return f"{self.state.state.name}"
