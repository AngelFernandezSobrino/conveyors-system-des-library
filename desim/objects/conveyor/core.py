from __future__ import annotations
import logging
from typing import TypedDict, TYPE_CHECKING
from desim.logger import (
    get_logger,
    LOGGER_BASE_NAME,
    LOGGER_CONVEYOR_NAME,
    LOGGER_NAME_PADDING,
    LOGGER_CONVEYOR_COLOR,
)

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


class Conveyor:
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
        self.container: Container | None = None

        # DEVS states and events
        self.input_events: events.InputEvents = events.InputEvents(self)
        self.output_events: events.OutputEvents = events.OutputEvents(self)
        self.states: states.State = states.State(self)

    def __str__(self) -> str:
        return f"Conveyor {self.id}"

    def set_origin(self, origin: desim.objects.stopper.core.Stopper) -> None:
        self.origin = origin

    def set_destiny(self, destiny: desim.objects.stopper.core.Stopper) -> None:
        self.destiny = destiny