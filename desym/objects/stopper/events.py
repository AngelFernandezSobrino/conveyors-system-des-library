from __future__ import annotations
import copy
from typing import TYPE_CHECKING

from wandb import _set_internal_process


from desym.objects.stopper.states import States

if TYPE_CHECKING:
    from desym.objects.container import Container
    from desym.objects.stopper import StopperId
    from . import core
    import desym.objects.conveyor
    import desym.objects.stopper

# This classes implement the events connections of the stoppers to other stoppers and to the behavior controller


class InputEvents:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

    def input(self, container: Container) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        if self.c.debug:
            print(f"{self.c} input {container}")
        match self.c.states.state:
            case States(States.Node.RESERVED):
                if self.c.container is not None:
                    raise Exception(
                        f"Fatal error: Tray is not None, WTF {self.c.container}"
                    )
                actual_state.node = States.Node.OCCUPIED
                self.c.container = container
                self.c.states.go_state(actual_state)
            case States(node=States.Node.REST) | States(
                node=States.Node.OCCUPIED
            ) | States(node=States.Node.SENDING):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, input event is not allowed"
                )
            case _:
                raise Exception(
                    f"Fatal error: Unknown state {self.c.states.state} in stopper {self.c.id}"
                )

    def reserve(self) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        match self.c.states.state:
            case States(node=States.Node.REST):
                if self.c.container is not None:
                    raise Exception(
                        f"Fatal error: Tray is not None, WTF {self.c.container}"
                    )
                actual_state.node = States.Node.RESERVED
                self.c.states.go_state(actual_state)
            case States(node=States.Node.RESERVED) | States(
                node=States.Node.OCCUPIED
            ) | States(node=States.Node.SENDING):
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, reserve event is not allowed"
                )
            case _:
                raise Exception(
                    f"Fatal error: Unknown state {self.c.states.state} in stopper {self.c.id}"
                )

    def destiny_available(
        self, destiny_conveyor_id: desym.objects.conveyor.ConveyorId
    ) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_conveyor_id:
                actual_state.destinies[destiny_id] = States.Destiny.AVAILABLE
                self.c.states.go_state(actual_state)

    def destiny_not_available(
        self, destiny_conveyor_id: desym.objects.stopper.StopperId
    ) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_conveyor_id:
                actual_state.destinies[destiny_id] = States.Destiny.NOT_AVAILABLE
                self.c.states.go_state(actual_state)

    def control_lock_by_destiny_id(
        self, destiny_id_to_lock: desym.objects.stopper.StopperId
    ) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        for destiny_id in self.c.output_conveyors:
            if destiny_id == destiny_id_to_lock:
                actual_state.control[destiny_id] = States.Control.LOCKED
                self.c.states.go_state(actual_state)

    def control_unlock_by_destiny_id(
        self, context, destiny_id_to_lock: desym.objects.stopper.StopperId
    ) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        for destiny_id in self.c.output_conveyors:
            if destiny_id == destiny_id_to_lock:
                actual_state.control[destiny_id] = States.Control.UNLOCKED
                self.c.states.go_state(actual_state)

    def control_lock_by_conveyor_id(
        self, destiny_destiny_id: desym.objects.conveyor.ConveyorId
    ) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_destiny_id:
                actual_state.control[destiny_id] = States.Control.LOCKED
                self.c.states.go_state(actual_state)

    def control_unlock_by_conveyor_id(
        self, destiny_conveyor_id: desym.objects.conveyor.ConveyorId
    ) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        for destiny_id, conveyor in self.c.output_conveyors.items():
            if conveyor.id == destiny_conveyor_id:
                actual_state.control[destiny_id] = States.Control.UNLOCKED
                self.c.states.go_state(actual_state)


# Output events class, used by the stopper to send events to other stoppers
class OutputEvents:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

    def not_available(self):
        for _, conveyor in self.c.input_conveyors.items():
            conveyor.input_events.destiny_not_available()

    def available(self):
        for _, conveyor in self.c.input_conveyors.items():
            conveyor.input_events.destiny_available()

    def output(self, destinyId: StopperId):
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")

        self.c.output_conveyors[destinyId].input_events.input()

    def moving(self, destinyId: StopperId):
        if self.c.debug:
            print(f"{self.c} output to {destinyId}")
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")
        container = self.c.container
        self.c.container = None
        self.c.output_conveyors[destinyId].input_events.moving(container)

    def end_state(self, old_state: States):
        if (
            old_state.node == States.Node.REST
            and old_state.node != self.c.states.state.node
        ):
            self.not_available()
        if (
            old_state.node == States.Node.OCCUPIED
            and old_state.node != self.c.states.state.node
        ):
            for destinyId, send in self.c.states.state.sends.items():
                if send == States.Send.ONGOING:
                    self.output(destinyId)
        if (
            old_state.node == States.Node.SENDING
            and old_state.node != self.c.states.state.node
        ):
            for destinyId, send in old_state.sends.items():
                if send == States.Send.DELAY:
                    self.moving(destinyId)
            self.available()
