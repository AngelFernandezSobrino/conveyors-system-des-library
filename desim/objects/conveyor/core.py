from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Generic, TypeVar

from desim.custom_logging import (
    get_logger,
    LOGGER_BASE_NAME,
    LOGGER_CONVEYOR_NAME,
    LOGGER_NAME_PADDING,
    LOGGER_CONVEYOR_COLOR,
)
from desim.objects.container import ContentType

from . import events, states

if TYPE_CHECKING:
    from desim.objects.container import Container
    import desim.objects.system
    import desim.objects.stopper.core
    import desim.events_manager
    import desim.objects.conveyor
    import desim.objects.stopper
    import desim.core


class ConveyorDescription(TypedDict):
    origin_id: desim.objects.stopper.StopperId
    destiny_id: desim.objects.stopper.StopperId
    steps: int


class Conveyor(Generic[ContentType]):
    def __init__(
        self,
        id: desim.objects.conveyor.ConveyorId,
        description: ConveyorDescription,
        simulation: desim.core.Simulation,
        debug,
    ):
        self.id = id
        self.description = description
        self.steps = description["steps"]
        self.debug = debug

        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME}.{self.id}",
            f"{LOGGER_CONVEYOR_COLOR}{LOGGER_BASE_NAME}.{LOGGER_CONVEYOR_NAME} - {self.id: <{LOGGER_NAME_PADDING}s} - ",
        )

        # Globals
        self.simulation = simulation
        self.events_manager: desim.events_manager.TimedEventsManager = (
            self.simulation.timed_events_manager
        )
        self.origin: desim.objects.stopper.core.Stopper
        self.destiny: desim.objects.stopper.core.Stopper

        # Container storage pointer
        self.container: Container[ContentType] | None = None

        # DEVS states and events
        self.i: events.InputEventsController = events.InputEventsController(self)
        self.o: events.OutputEventsController = events.OutputEventsController(self)
        self.s: states.StateController = states.StateController(self)

    def __str__(self) -> str:
        return f"Conveyor {self.id}"

    def set_origin(self, origin: desim.objects.stopper.core.Stopper) -> None:
        self.origin = origin

    def set_destiny(self, destiny: desim.objects.stopper.core.Stopper) -> None:
        self.destiny = destiny

    def dump(self):
        return f"Conveyor {self.id} - {self.s.dump()}"
