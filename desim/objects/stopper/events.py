from __future__ import annotations
import copy
import logging
from typing import TYPE_CHECKING

from desim.objects.stopper.states import StateModel, StateModelChange

from desim.custom_logging import (
    LOGGER_BASE_NAME,
    LOGGER_INPUT_EVENT_COLOR,
    LOGGER_INPUT_GROUP_NAME,
    LOGGER_NAME_PADDING,
    LOGGER_OUTPUT_EVENT_COLOR,
    LOGGER_OUTPUT_GROUP_NAME,
    LOGGER_STOPPER_COLOR,
    LOGGER_STOPPER_NAME,
    get_logger,
)

if TYPE_CHECKING:
    from desim.objects.container import Container
    from desim.objects.stopper import StopperId
    from . import core
    import desim.objects.conveyor
    import desim.objects.stopper

# This classes implement the events connections of the stoppers to other stoppers and to the behavior controller


class InputEventsController:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_STOPPER_NAME}.{self.c.id}.evins",
            f"{LOGGER_STOPPER_COLOR}{LOGGER_BASE_NAME}.{LOGGER_STOPPER_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_INPUT_EVENT_COLOR}{LOGGER_INPUT_GROUP_NAME} - ",
        )

    def reserve(self) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Reserved by input conveyor")

        if self.c.s.state.node != StateModel.Node.REST:
            raise Exception(
                f"Fatal error: Actual state is {self.c.s.state}, reserve event is not allowed"
            )

        if self.c.container is not None:
            raise Exception(f"Fatal error: Tray is not None, WTF {self.c.container}")

        self.c.s.go_state(StateModelChange(node=StateModel.Node.RESERVED))

    def receive(self, container: Container) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug(f"Receive container {container}")
        if self.c.s.state.node != StateModel.Node.RESERVED:
            raise Exception(
                f"Fatal error: Actual state is {self.c.s.state}, receive event is not allowed"
            )
        if self.c.container is not None:
            raise Exception("Fatal error: Tray is None, WTF")

        self.c.container = container
        self.c.s.go_state(StateModelChange(node=StateModel.Node.OCCUPIED))

    def destiny_available(
        self, destiny_conveyor_id: desim.objects.conveyor.ConveyorId
    ) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Destiny is available")

        for destiny_id, conveyor in self.c.output_conveyors_by_destiny_id.items():
            if conveyor.id == destiny_conveyor_id:
                self.c.s.go_state(StateModelChange(destinies={destiny_id: StateModel.Destiny.AVAILABLE}))

    def destiny_not_available(
        self, destiny_conveyor_id: desim.objects.stopper.StopperId
    ) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Destiny isn't available")

        for destiny_id, conveyor in self.c.output_conveyors_by_destiny_id.items():
            if conveyor.id == destiny_conveyor_id:
                self.c.s.go_state_destiny_not_available(destiny_id)

    def control_lock_by_destiny_id(
        self, destiny_id_to_lock: desim.objects.stopper.StopperId
    ) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Control lock")

        self.c.s.go_state_control_lock(destiny_id_to_lock)

    def control_unlock_by_destiny_id(
        self, context, destiny_id_to_lock: desim.objects.stopper.StopperId
    ) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Control unlock")

        if self.c.s.state.control[destiny_id_to_lock] == StateModel.Control.UNLOCKED:
            return

        self.c.s.go_state(StateModelChange(control={destiny_id_to_lock: StateModel.Control.UNLOCKED}))

    def control_lock_by_conveyor_id(
        self, destiny_conveyor_id_to_lock: desim.objects.conveyor.ConveyorId
    ) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Control lock")

        for destiny_id, conveyor in self.c.output_conveyors_by_destiny_id.items():
            if conveyor.id == destiny_conveyor_id_to_lock:
                self.c.s.go_state_control_lock(destiny_id)
                return

    def control_unlock_by_conveyor_id(
        self, destiny_conveyor_id_to_unlock: desim.objects.conveyor.ConveyorId
    ) -> None:
        if self.logger.level == logging.DEBUG: self.logger.debug("Control unlock")

        for destiny_id, conveyor in self.c.output_conveyors_by_destiny_id.items():
            if conveyor.id == destiny_conveyor_id_to_unlock:
                if self.c.s.state.control[destiny_id] == StateModel.Control.UNLOCKED:
                    return
                self.c.s.go_state(StateModelChange(control={destiny_id: StateModel.Control.UNLOCKED}))
                return


# Output events class, used by the stopper to send events to other stoppers
class OutputEventsController:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_STOPPER_NAME}.{self.c.id}.evout",
            f"{LOGGER_STOPPER_COLOR}{LOGGER_BASE_NAME}.{LOGGER_STOPPER_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_OUTPUT_EVENT_COLOR}{LOGGER_OUTPUT_GROUP_NAME} - ",
        )

    def reserve(self, destinyId: StopperId):
        if self.logger.level == logging.DEBUG: self.logger.debug(f"Reserve {destinyId}")
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")

        self.c.output_conveyors_by_destiny_id[destinyId].i.reserve()

    def send(self, destiny_id: StopperId):
        if self.logger.level == logging.DEBUG: self.logger.debug(f"Send {self.c.container} to {destiny_id}")
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")
        container = self.c.container
        self.c.container = None
        self.c.output_conveyors_by_destiny_id[destiny_id].i.receive(container)

    def available(self):
        if self.logger.level == logging.DEBUG: self.logger.debug("I'm available")
        for conveyor in self.c.input_conveyors_by_destiny_id.values():
            if self.c.s.state.node == StateModel.Node.REST:
                conveyor.i.destiny_available()

    def not_available(self):
        if self.logger.level == logging.DEBUG: self.logger.debug("I'm not available")
        for conveyor in self.c.input_conveyors_by_destiny_id.values():
            conveyor.i.destiny_not_available()
