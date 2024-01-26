from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import core
    from .states import States
    import desym.objects.container

# This classes implement the events connections of the stoppers to other stoppers and to the behavior controller


class InputEvents:
    def __init__(self, core: core.Conveyor) -> None:
        self.c = core

    def destiny_available(self) -> None:
        match self.c.states.state:
            case States.NOT_AVAILABLE:
                self.c.states.go_state(States.AVAILABLE)
            case States.AVAILABLE, States.NOT_AVAILABLE_BY_DESTINY, States.NOT_AVAILABLE_BY_MOVING, States.MOVING:
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, destiny_not_available event is not allowed"
                )
            case _:
                raise Exception(
                    f"Fatal error: Unknown state {self.c.states.state} in conveyor {self.c.id}"
                )

    def destiny_not_available(self) -> None:
        match self.c.states.state:
            case States.AVAILABLE:
                self.c.states.go_state(States.NOT_AVAILABLE_BY_DESTINY)
            case States.NOT_AVAILABLE_BY_DESTINY, States.NOT_AVAILABLE_BY_MOVING, States.MOVING, States.NOT_AVAILABLE:
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, destiny_not_available event is not allowed"
                )
            case _:
                raise Exception(
                    f"Fatal error: Unknown state {self.c.states.state} in conveyor {self.c.id}"
                )

    def input(self) -> None:
        match self.c.states.state:
            case States.AVAILABLE:
                self.c.states.go_state(States.NOT_AVAILABLE_BY_MOVING)
            case States.NOT_AVAILABLE_BY_DESTINY, States.NOT_AVAILABLE_BY_MOVING, States.MOVING, States.NOT_AVAILABLE:
                raise Exception(
                    f"Fatal error: Actual state is {self.c.states.state}, destiny_not_available event is not allowed"
                )
            case _:
                raise Exception(
                    f"Fatal error: Unknown state {self.c.states.state} in conveyor {self.c.id}"
                )

    def moving(self, container: desym.objects.container.Container) -> None:
        match self.c.states.state:
            case States.NOT_AVAILABLE_BY_MOVING:
                self.c.container = container
                self.c.states.go_state(States.MOVING)
            case States.AVAILABLE, States.NOT_AVAILABLE_BY_DESTINY, States.MOVING, States.NOT_AVAILABLE:
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

    def output(self) -> None:
        if self.c.container is None:
            raise Exception("Fatal Error: Tray is None, WTF")
        container = self.c.container
        self.c.container = None
        self.c.destiny.input_events.input(container)

    def not_available(self) -> None:
        self.c.origin.input_events.destiny_not_available(self.c.id)

    def available(self) -> None:
        self.c.origin.input_events.destiny_available(self.c.id)

    def destiny_reserve(self) -> None:
        self.c.destiny.input_events.reserve()

    def end_state(self, state: States) -> None:
        match state:
            case States.AVAILABLE:
                pass
            case States.NOT_AVAILABLE_BY_DESTINY:
                self.not_available()
            case States.NOT_AVAILABLE_BY_MOVING:
                self.not_available()
                self.destiny_reserve()
            case States.MOVING:
                self.output()
            case States.NOT_AVAILABLE:
                self.available()
            case _:
                raise Exception(f"Fatal error: Unknown state {state}")
