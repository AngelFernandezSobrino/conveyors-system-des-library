from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from desim.logger import LOGGER_BASE_NAME, LOGGER_CONVEYOR_COLOR, LOGGER_CONVEYOR_NAME, LOGGER_INPUT_EVENT_COLOR, LOGGER_INPUT_GROUP_NAME, LOGGER_NAME_PADDING, LOGGER_OUTPUT_EVENT_COLOR, get_logger  # type: ignore

from .states import States

if TYPE_CHECKING:
    from . import core
    import desim.objects.container


# This classes implement the events connections of the stoppers to other stoppers and to the behavior controller
class InputEvents:
    def __init__(self, core: core.Conveyor) -> None:
        self.c = core
        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME}.{self.c.id}.evout",
            f"{LOGGER_CONVEYOR_COLOR}{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_INPUT_EVENT_COLOR}{LOGGER_INPUT_GROUP_NAME} - ",
        )

    def destiny_available(self) -> None:
        self.logger.debug("Destiny available")
        match self.c.states.state:
            case States(States.S.NOT_AVAILABLE):
                self.c.states.go_state(None, States(States.S.AVAILABLE))
            case States(States.S.AVAILABLE), States(
                States.S.NOT_AVAILABLE_BY_DESTINY
            ), States(States.S.NOT_AVAILABLE_BY_MOVING), States(States.S.MOVING):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, destiny_not_available event is not allowed"
                )
            case _:
                raise Exception(
                    f"Fatal error: Unknown state {self.c.states.state} in conveyor {self.c.id}"
                )

    def destiny_not_available(self) -> None:
        self.logger.debug("Destiny not available")
        match self.c.states.state:
            case States(States.S.AVAILABLE):
                self.c.states.go_state(None, States(States.S.NOT_AVAILABLE_BY_DESTINY))
            case States(
                States.S.NOT_AVAILABLE_BY_DESTINY
                | States.S.NOT_AVAILABLE_BY_MOVING
                | States.S.MOVING
                | States.S.NOT_AVAILABLE
            ):
                pass
                # raise Exception(
                #     f"Fatal error: Actual state is {self.c.states.state}, destiny_not_available event is not allowed"
                # )
            case _:
                raise Exception(
                    f"Fatal error: Unknown state {self.c.states.state} in conveyor {self.c.id}"
                )

    def reserve(self) -> None:
        self.logger.debug("Reserve")
        match self.c.states.state:
            case States(States.S.AVAILABLE):
                self.c.states.go_state(None, States(States.S.NOT_AVAILABLE_BY_MOVING))
            case States(
                States.S.NOT_AVAILABLE_BY_DESTINY
                | States.S.NOT_AVAILABLE_BY_MOVING
                | States.S.MOVING
                | States.S.NOT_AVAILABLE
            ):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, destiny_not_available event is not allowed"
                )
            case _:
                raise Exception(
                    f"Fatal error: Unknown state {self.c.states.state} in conveyor {self.c.id}"
                )

    def input(self, container: desim.objects.container.Container) -> None:
        self.logger.debug("Input")
        match self.c.states.state:
            case States(States.S.MOVING):
                self.c.container = container
            case States(
                States.S.AVAILABLE
                | States.S.NOT_AVAILABLE_BY_DESTINY
                | States.S.NOT_AVAILABLE_BY_MOVING
                | States.S.NOT_AVAILABLE
            ):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, destiny_not_available event is not allowed"
                )
            case _:
                raise Exception(
                    f"Fatal error: Unknown state {self.c.states.state} in conveyor {self.c.id}"
                )


# Output events class, used by the stopper to send events to other stoppers
class OutputEvents:
    def __init__(self, core: core.Conveyor) -> None:
        self.c = core

        self.logger = logging.getLogger(f"desim.conv.{self.c.id}.evout")
        self.logger.propagate = False
        logFormatter = logging.Formatter(
            f"{LOGGER_CONVEYOR_COLOR}desim.conv - {self.c.id: <10s} - {LOGGER_OUTPUT_EVENT_COLOR}Output - "
            + "{message}",
            style="{",
        )
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        self.logger.addHandler(consoleHandler)

    def output(self) -> None:
        self.logger.debug("Output")
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")
        container = self.c.container
        self.c.container = None
        self.c.destiny.input_events.input(container)

    def not_available(self) -> None:
        self.logger.debug("Not available")
        self.c.origin.input_events.destiny_not_available(self.c.id)

    def available(self) -> None:
        self.logger.debug("Available")
        self.c.origin.input_events.destiny_available(self.c.id)

    def reserve(self) -> None:
        self.logger.debug("Reserve destiny")
        self.c.destiny.input_events.reserve()

    def end_state(self, state: States) -> None:
        match state:
            case States(States.S.AVAILABLE):
                pass
            case States(States.S.NOT_AVAILABLE_BY_DESTINY):
                self.not_available()
            case States(States.S.NOT_AVAILABLE_BY_MOVING):
                self.not_available()
                self.reserve()
            case States(States.S.MOVING):
                self.output()
            case States(States.S.NOT_AVAILABLE):
                self.available()
            case _:
                raise Exception(f"Fatal error: Unknown state {state}")
