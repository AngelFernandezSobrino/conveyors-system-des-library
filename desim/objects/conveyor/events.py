from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from desim.custom_logging import LOGGER_BASE_NAME, LOGGER_CONVEYOR_COLOR, LOGGER_CONVEYOR_NAME, LOGGER_INPUT_EVENT_COLOR, LOGGER_INPUT_GROUP_NAME, LOGGER_NAME_PADDING, LOGGER_OUTPUT_EVENT_COLOR, LOGGER_OUTPUT_GROUP_NAME, get_logger  # type: ignore

from .states import States

if TYPE_CHECKING:
    from . import core
    import desim.objects.container


# This classes implement the events connections of the stoppers to other stoppers and to the behavior controller
class InputEvents:
    def __init__(self, core: core.Conveyor) -> None:
        self.c = core
        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME}.{self.c.id}.event_input",
            f"{LOGGER_CONVEYOR_COLOR}{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_INPUT_EVENT_COLOR}{LOGGER_INPUT_GROUP_NAME} - ",
        )

    def reserve(self) -> None:
        self.logger.debug("Reserved by origin")
        match self.c.states.state:
            case States(States.S.AVAILABLE):
                self.c.states.go_state(None, States(States.S.NOT_AVAILABLE_BY_MOVING))
            case States(
                States.S.NOT_AVAILABLE_BY_MOVING
                | States.S.WAITING_RECEIVE
                | States.S.MOVING
                | States.S.NOT_AVAILABLE
            ):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, reserve event is not allowed"
                )

    def receive(self, container: desim.objects.container.Container) -> None:
        self.logger.debug(f"Receive {container}")
        match self.c.states.state:
            case States(States.S.WAITING_RECEIVE):
                self.c.container = container
                self.c.states.go_state(None, States(States.S.MOVING))
            case States(
                States.S.AVAILABLE
                | States.S.MOVING
                | States.S.NOT_AVAILABLE_BY_MOVING
                | States.S.NOT_AVAILABLE
            ):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, receive event is not allowed"
                )

    def destiny_available(self) -> None:
        self.logger.debug("Destiny is available")
        match self.c.states.state:
            case States(States.S.NOT_AVAILABLE):
                self.c.states.go_state(None, States(States.S.AVAILABLE))
            case States(
                States.S.NOT_AVAILABLE_BY_MOVING
                | States.S.MOVING
                | States.S.WAITING_RECEIVE
            ):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, destiny_available event is not allowed"
                )

    def destiny_not_available(self) -> None:
        self.logger.debug("Destiny isn't available")
        match self.c.states.state:
            case States(States.S.AVAILABLE):
                self.c.states.go_state(None, States(States.S.NOT_AVAILABLE))
            case States(States.S.MOVING):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, destiny_not_available event is not allowed"
                )


# Output events class, used by the stopper to send events to other stoppers
class OutputEvents:
    def __init__(self, core: core.Conveyor) -> None:
        self.c = core
        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME}.{self.c.id}.evout",
            f"{LOGGER_CONVEYOR_COLOR}{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_OUTPUT_EVENT_COLOR}{LOGGER_OUTPUT_GROUP_NAME} - ",
        )

    def reserve(self) -> None:
        self.logger.debug("Reserve destiny")
        self.c.destiny.input_events.reserve()

    def send(self) -> None:
        self.logger.debug(f"Send {self.c.container} to destiny")
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")
        container = self.c.container
        self.c.container = None
        self.c.destiny.input_events.receive(container)

    def available(self) -> None:
        self.logger.debug("Available to origin")
        self.c.origin.input_events.destiny_available(self.c.id)

    def not_available(self) -> None:
        self.logger.debug("Not available to origin")
        self.c.origin.input_events.destiny_not_available(self.c.id)

    def end_state(self, state: States) -> None:
        match state:
            case States(States.S.AVAILABLE):
                self.not_available()
            case States(States.S.NOT_AVAILABLE_BY_MOVING):
                self.reserve()
            case States(States.S.MOVING):
                self.send()
            case States(States.S.NOT_AVAILABLE):
                self.available()
            case States(States.S.WAITING_RECEIVE):
                pass
            case _:
                raise Exception(f"Fatal error: Unknown state {state}")
