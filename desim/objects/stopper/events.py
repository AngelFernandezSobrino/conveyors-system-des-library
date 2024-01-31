from __future__ import annotations
import copy
import logging
from typing import TYPE_CHECKING

from desim.objects.stopper.states import States

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


class InputEvents:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_STOPPER_NAME}.{self.c.id}.evins",
            f"{LOGGER_STOPPER_COLOR}{LOGGER_BASE_NAME}.{LOGGER_STOPPER_NAME} - {self.c.id: <{LOGGER_NAME_PADDING}s} - {LOGGER_INPUT_EVENT_COLOR}{LOGGER_INPUT_GROUP_NAME} - ",
        )

    def reserve(self) -> None:
        self.logger.debug("Reserved by input conveyor")
        actual_state = copy.deepcopy(self.c.states.state)
        match self.c.states.state:
            case States(node=States.Node.REST):
                if self.c.container is not None:
                    raise Exception(
                        f"Fatal error: Tray is not None, WTF {self.c.container}"
                    )
                actual_state.node = States.Node.RESERVED
                self.c.states.go_state(actual_state)
            case (
                States(node=States.Node.RESERVED)
                | States(node=States.Node.OCCUPIED)
                | States(node=States.Node.SENDING)
            ):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, reserve event is not allowed"
                )

    def receive(self, container: Container) -> None:
        self.logger.debug(f"Receive container {container}")
        actual_state = copy.deepcopy(self.c.states.state)
        match self.c.states.state:
            case States(States.Node.RESERVED):
                if self.c.container is not None:
                    raise Exception(
                        f"Fatal error: Tray is not None, WTF {self.c.container}"
                    )
                actual_state.node = States.Node.OCCUPIED
                self.c.container = container
                self.c.states.go_state(actual_state)
            case (
                States(node=States.Node.REST)
                | States(node=States.Node.OCCUPIED)
                | States(node=States.Node.SENDING)
            ):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, input event is not allowed"
                )

    def destiny_available(
        self, destiny_conveyor_id: desim.objects.conveyor.ConveyorId
    ) -> None:
        self.logger.debug("Destiny is available")
        actual_state = copy.deepcopy(self.c.states.state)
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_conveyor_id:
                actual_state.destinies[destiny_id] = States.Destiny.AVAILABLE

        self.c.states.go_state(actual_state)

    def destiny_not_available(
        self, destiny_conveyor_id: desim.objects.stopper.StopperId
    ) -> None:
        self.logger.debug("Destiny isn't available")
        actual_state = copy.deepcopy(self.c.states.state)
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_conveyor_id:
                actual_state.destinies[destiny_id] = States.Destiny.NOT_AVAILABLE

        self.c.states.go_state(actual_state)

    def control_lock_by_destiny_id(
        self, destiny_id_to_lock: desim.objects.stopper.StopperId
    ) -> None:
        self.logger.debug("Control lock")

        if self.c.states.state.control[destiny_id_to_lock] == States.Control.LOCKED:
            return
        actual_state = copy.deepcopy(self.c.states.state)
        actual_state.control[destiny_id_to_lock] = States.Control.LOCKED
        self.c.states.go_state(actual_state, False)

    def control_unlock_by_destiny_id(
        self, context, destiny_id_to_lock: desim.objects.stopper.StopperId
    ) -> None:
        self.logger.debug("Control unlock")

        if self.c.states.state.control[destiny_id_to_lock] == States.Control.UNLOCKED:
            return
        actual_state = copy.deepcopy(self.c.states.state)
        actual_state.control[destiny_id_to_lock] = States.Control.UNLOCKED
        self.c.states.go_state(actual_state)

    def control_lock_by_conveyor_id(
        self, destiny_conveyor_id_to_lock: desim.objects.conveyor.ConveyorId
    ) -> None:
        self.logger.debug("Control lock")
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_conveyor_id_to_lock:
                if self.c.states.state.control[destiny_id] == States.Control.LOCKED:
                    return
                actual_state = copy.deepcopy(self.c.states.state)
                actual_state.control[destiny_id] = States.Control.LOCKED
                self.c.states.go_state(actual_state, False)
                return

    def control_unlock_by_conveyor_id(
        self, destiny_conveyor_id_to_unlock: desim.objects.conveyor.ConveyorId
    ) -> None:
        self.logger.debug("Control unlock")
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_conveyor_id_to_unlock:
                if self.c.states.state.control[destiny_id] == States.Control.UNLOCKED:
                    return
                actual_state = copy.deepcopy(self.c.states.state)
                actual_state.control[destiny_id] = States.Control.UNLOCKED
                self.c.states.go_state(actual_state)
                return


# Output events class, used by the stopper to send events to other stoppers
class OutputEvents:
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

        self.c.output_conveyors[destinyId].input_events.reserve()

    def send(self, destinyId: StopperId):
        self.logger.debug(f"Send {self.c.container} to {destinyId}")
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")
        container = self.c.container
        self.c.container = None
        self.c.output_conveyors[destinyId].input_events.receive(container)

    def available(self):
        self.logger.debug("I'm available")
        for conveyor in self.c.input_conveyors.values():
            conveyor.input_events.destiny_available()

    def not_available(self):
        self.logger.debug("I'm not available")
        for conveyor in self.c.input_conveyors.values():
            conveyor.input_events.destiny_not_available()

    def end_state(self, old_state: States):
        if (
            old_state.node == States.Node.REST
            and old_state.node != self.c.states.state.node
        ):
            self.not_available()
            return
        if (
            old_state.node == States.Node.OCCUPIED
            and old_state.node != self.c.states.state.node
        ):
            for destinyId, send in self.c.states.state.sends.items():
                if send == States.Send.ONGOING:
                    self.reserve(destinyId)
                    return
        if (
            old_state.node == States.Node.SENDING
            and old_state.node != self.c.states.state.node
        ):
            for destinyId, send in old_state.sends.items():
                if send == States.Send.DELAY:
                    self.send(destinyId)
            self.available()
            return
