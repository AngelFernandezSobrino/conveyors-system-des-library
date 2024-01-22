from __future__ import annotations
import copy
from typing import TYPE_CHECKING

from wandb import _set_internal_process


from desym.objects.container import Container
from desym.objects.conveyor.core import Conveyor
from desym.objects.stopper.states import States

if TYPE_CHECKING:
    from . import core
    from desym.objects.stopper.core import Stopper

# This classes implement the events connections of the stoppers to other stoppers and to the behavior controller


class InputEvents:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

    def input(self, container: Container) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        match self.c.states.state:
            case States.Node.RESERVED:
                actual_state.node = States.Node.OCCUPIED
                self.c.states.go_state(actual_state)
            case States.Node.RESERVED, States.Node.SENDING, States.Node.OCCUPIED:
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
            case States.Node.REST:
                actual_state.node = States.Node.RESERVED
                self.c.states.go_state(actual_state)
            case States.Node.RESERVED, States.Node.OCCUPIED, States.Node.SENDING:
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, reserve event is not allowed"
                )
            case _:
                raise Exception(
                    f"Fatal error: Unknown state {self.c.states.state} in stopper {self.c.id}"
                )

    def destiny_available(self, conveyor_id: Conveyor.ConeyorId) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        for index, conveyor in enumerate(self.c.output_conveyors):
            if conveyor.id == conveyor_id:
                actual_state.destinies[index] = States.Destiny.AVAILABLE
                self.c.states.go_state(actual_state)

    def destiny_not_available(self, conveyor_id: Conveyor.ConeyorId) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        for index, conveyor in enumerate(self.c.output_conveyors):
            if conveyor.id == conveyor_id:
                actual_state.destinies[index] = States.Destiny.NOT_AVAILABLE
                self.c.states.go_state(actual_state)

    def control_lock(self, conveyor_id: Conveyor.ConeyorId) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        for index, conveyor in enumerate(self.c.output_conveyors):
            if conveyor.id == conveyor_id:
                actual_state.control[index] = States.Control.LOCKED
                self.c.states.go_state(actual_state)

    def control_unlock(self, conveyor_id: Conveyor.ConeyorId) -> None:
        actual_state = copy.deepcopy(self.c.states.state)
        for index, conveyor in enumerate(self.c.output_conveyors):
            if conveyor.id == conveyor_id:
                actual_state.control[index] = States.Control.UNLOCKED
                self.c.states.go_state(actual_state)


# Output events class, used by the stopper to send events to other stoppers
class OutputEvents:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

    def not_available(self):
        for conveyor in self.c.input_conveyors:
            conveyor.input_events.destiny_not_available()

    def available(self):
        for conveyor in self.c.input_conveyors:
            conveyor.input_events.destiny_available()

    def output(self, index: int):
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")
        self.c.output_conveyors[index].input_events.input()

    def moving(self, index: int):
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")
        container = self.c.container
        self.c.container = None
        self.c.output_conveyors[index].input_events.moving(container)

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
            for index, send in enumerate(self.c.states.state.sends):
                if send == States.Send.ONGOING:
                    self.output(index)
        if (
            old_state.node == States.Node.SENDING
            and old_state.node != self.c.states.state.node
        ):
            for index, send in enumerate(old_state.sends):
                if send == States.Send.DELAY:
                    self.moving(index)
            self.available()
