from __future__ import annotations
import copy
import logging
from typing import TYPE_CHECKING

from desim.objects.stopper.states import StateModel

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
        self.logger.debug("Reserved by input conveyor")
        actual_state = copy.deepcopy(self.c.s.state)
        match self.c.s.state:
            case StateModel(node=StateModel.Node.REST):
                if self.c.container is not None:
                    raise Exception(
                        f"Fatal error: Tray is not None, WTF {self.c.container}"
                    )
                actual_state.node = StateModel.Node.RESERVED
                self.c.s.go_state(actual_state)
            case (
                StateModel(node=StateModel.Node.RESERVED)
                | StateModel(node=StateModel.Node.OCCUPIED)
                | StateModel(node=StateModel.Node.SENDING)
            ):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.s.state}, reserve event is not allowed"
                )

    def receive(self, container: Container) -> None:
        self.logger.debug(f"Receive container {container}")
        actual_state = copy.deepcopy(self.c.s.state)
        match self.c.s.state:
            case StateModel(StateModel.Node.RESERVED):
                if self.c.container is not None:
                    raise Exception(
                        f"Fatal error: Tray is not None, WTF {self.c.container}"
                    )
                actual_state.node = StateModel.Node.OCCUPIED
                self.c.container = container
                self.c.s.go_state(actual_state)
            case (
                StateModel(node=StateModel.Node.REST)
                | StateModel(node=StateModel.Node.OCCUPIED)
                | StateModel(node=StateModel.Node.SENDING)
            ):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.s.state}, input event is not allowed"
                )

    def destiny_available(
        self, destiny_conveyor_id: desim.objects.conveyor.ConveyorId
    ) -> None:
        self.logger.debug("Destiny is available")
        actual_state = copy.deepcopy(self.c.s.state)
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_conveyor_id:
                actual_state.destinies[destiny_id] = StateModel.Destiny.AVAILABLE

        self.c.s.go_state(actual_state)

    def destiny_not_available(
        self, destiny_conveyor_id: desim.objects.stopper.StopperId
    ) -> None:
        self.logger.debug("Destiny isn't available")
        actual_state = copy.deepcopy(self.c.s.state)
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_conveyor_id:
                actual_state.destinies[destiny_id] = StateModel.Destiny.NOT_AVAILABLE

        self.c.s.go_state(actual_state)

    def control_lock_by_destiny_id(
        self, destiny_id_to_lock: desim.objects.stopper.StopperId
    ) -> None:
        self.logger.debug("Control lock")

        if self.c.s.state.control[destiny_id_to_lock] == StateModel.Control.LOCKED:
            return
        actual_state = copy.deepcopy(self.c.s.state)
        actual_state.control[destiny_id_to_lock] = StateModel.Control.LOCKED
        self.c.s.go_state(actual_state, False)

    def control_unlock_by_destiny_id(
        self, context, destiny_id_to_lock: desim.objects.stopper.StopperId
    ) -> None:
        self.logger.debug("Control unlock")

        if self.c.s.state.control[destiny_id_to_lock] == StateModel.Control.UNLOCKED:
            return
        actual_state = copy.deepcopy(self.c.s.state)
        actual_state.control[destiny_id_to_lock] = StateModel.Control.UNLOCKED
        self.c.s.go_state(actual_state)

    def control_lock_by_conveyor_id(
        self, destiny_conveyor_id_to_lock: desim.objects.conveyor.ConveyorId
    ) -> None:
        self.logger.debug("Control lock")
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_conveyor_id_to_lock:
                if self.c.s.state.control[destiny_id] == StateModel.Control.LOCKED:
                    return
                actual_state = copy.deepcopy(self.c.s.state)
                actual_state.control[destiny_id] = StateModel.Control.LOCKED
                self.c.s.go_state(actual_state, False)
                return

    def control_unlock_by_conveyor_id(
        self, destiny_conveyor_id_to_unlock: desim.objects.conveyor.ConveyorId
    ) -> None:
        self.logger.debug("Control unlock")
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_conveyor_id_to_unlock:
                if self.c.s.state.control[destiny_id] == StateModel.Control.UNLOCKED:
                    return
                actual_state = copy.deepcopy(self.c.s.state)
                actual_state.control[destiny_id] = StateModel.Control.UNLOCKED
                self.c.s.go_state(actual_state)
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
        self.logger.debug(f"Reserve {destinyId}")
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")

        self.c.output_conveyors[destinyId].i.reserve()

    def send(self, destinyId: StopperId):
        self.logger.debug(f"Send {self.c.container} to {destinyId}")
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")
        container = self.c.container
        self.c.container = None
        self.c.output_conveyors[destinyId].i.receive(container)

    def available(self):
        self.logger.debug("I'm available")
        for conveyor in self.c.input_conveyors.values():
            conveyor.i.destiny_available()

    def not_available(self):
        self.logger.debug("I'm not available")
        for conveyor in self.c.input_conveyors.values():
            conveyor.i.destiny_not_available()

    def end_state(self, old_state: StateModel):
        if (
            old_state.node == StateModel.Node.REST
            and old_state.node != self.c.s.state.node
        ):
            self.not_available()
            return
        if (
            old_state.node == StateModel.Node.OCCUPIED
            and old_state.node != self.c.s.state.node
        ):
            for destinyId, send in self.c.s.state.sends.items():
                if send == StateModel.Send.ONGOING:
                    self.reserve(destinyId)
                    return
        if (
            old_state.node == StateModel.Node.SENDING
            and old_state.node != self.c.s.state.node
        ):
            for destinyId, send in old_state.sends.items():
                if send == StateModel.Send.DELAY:
                    self.send(destinyId)
            self.available()
            return
