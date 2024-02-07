from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from desim.custom_logging import LOGGER_BASE_NAME, LOGGER_CONVEYOR_COLOR, LOGGER_CONVEYOR_NAME, LOGGER_INPUT_EVENT_COLOR, LOGGER_INPUT_GROUP_NAME, LOGGER_NAME_PADDING, LOGGER_OUTPUT_EVENT_COLOR, LOGGER_OUTPUT_GROUP_NAME, get_logger  # type: ignore

from .states import StateModel

if TYPE_CHECKING:
    from . import core
    import desim.objects.container


# This classes implement the events connections of the stoppers to other stoppers and to the behavior controller
class InputEventsController:
    def __init__(self, core: core.Conveyor) -> None:
        self.c = core
        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME}.{self.c.id}.event_input",
            f"{LOGGER_CONVEYOR_COLOR}{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_INPUT_EVENT_COLOR}{LOGGER_INPUT_GROUP_NAME} - ",
        )

    def reserve(self) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Reserved by origin")
        if self.c.s.state.state != StateModel.S.AVAILABLE:
            raise Exception(
                f"Fatal error: Actual state is {self.c.s.state}, reserve event is not allowed"
            )

        self.c.s.go_state(None, StateModel(StateModel.S.NOT_AVAILABLE_BY_MOVING))

    def receive(self, container: desim.objects.container.Container) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug(f"Receive {container}")
        if self.c.s.state.state != StateModel.S.WAITING_RECEIVE:
            raise Exception(
                f"Fatal error: Actual state is {self.c.s.state}, receive event is not allowed"
            )

        self.c.container = container
        self.c.s.go_state(None, StateModel(StateModel.S.MOVING))

    def destiny_available(self) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Destiny is available")
        if (
            self.c.s.state.state != StateModel.S.NOT_AVAILABLE
            and self.c.s.state.state != StateModel.S.AVAILABLE
        ):
            raise Exception(
                f"Fatal error: Actual state is {self.c.s.state}, destiny_available event is not allowed"
            )

        if self.c.s.state.state == StateModel.S.AVAILABLE:
            return

        self.c.s.go_state(None, StateModel(StateModel.S.AVAILABLE))

    def destiny_not_available(self) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Destiny isn't available")
        if (
            self.c.s.state.state != StateModel.S.AVAILABLE
            and self.c.s.state.state != StateModel.S.WAITING_RECEIVE
            and self.c.s.state.state != StateModel.S.NOT_AVAILABLE
        ):
            raise Exception(
                f"Fatal error: Actual state is {self.c.s.state}, destiny_not_available event is not allowed"
            )

        if (
            self.c.s.state.state == StateModel.S.WAITING_RECEIVE
            or self.c.s.state.state == StateModel.S.NOT_AVAILABLE
        ):
            return

        self.c.s.go_state(None, StateModel(StateModel.S.NOT_AVAILABLE))


# Output events class, used by the stopper to send events to other stoppers
class OutputEventsController:
    def __init__(self, core: core.Conveyor) -> None:
        self.c = core
        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME}.{self.c.id}.evout",
            f"{LOGGER_CONVEYOR_COLOR}{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_OUTPUT_EVENT_COLOR}{LOGGER_OUTPUT_GROUP_NAME} - ",
        )

    def reserve(self) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Reserve destiny")
        self.c.destiny.i.reserve()

    def send(self) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug(f"Send {self.c.container} to destiny")
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")
        container = self.c.container
        self.c.container = None
        self.c.destiny.i.receive(container)

    def available(self) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Available to origin")
        self.c.origin.i.destiny_available(self.c.id)

    def not_available(self) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Not available to origin")
        self.c.origin.i.destiny_not_available(self.c.id)

    def end_state(self, state: StateModel) -> None:
        match state:
            case StateModel(StateModel.S.AVAILABLE):
                pass
                self.not_available()
            case StateModel(StateModel.S.NOT_AVAILABLE_BY_MOVING):
                self.reserve()
            case StateModel(StateModel.S.MOVING):
                self.send()
            case StateModel(StateModel.S.NOT_AVAILABLE):
                self.available()
            case StateModel(StateModel.S.WAITING_RECEIVE):
                pass
            case _:
                raise Exception(f"Fatal error: Unknown state {state}")
