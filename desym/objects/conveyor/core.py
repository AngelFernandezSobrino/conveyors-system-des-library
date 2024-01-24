from __future__ import annotations
from typing import TypedDict, TYPE_CHECKING, Union

from desym.objects.container import Container
from . import events
from . import states

if TYPE_CHECKING:
    import desym.objects.system
    import desym.objects.stopper.core
    import desym.timed_events_manager

import desym.core


class ConveyorDescription(TypedDict):
    origin_id: desym.objects.stopper.TypeId
    destiny_id: desym.objects.stopper.TypeId
    steps: int


class Conveyor:
    ConveyorId = Union[str, str]

    def __init__(
        self,
        id: str,
        description: ConveyorDescription,
        simulation: desym.core.Simulation,
        debug,
    ):
        self.id = id
        self.description = description
        self.steps = description["steps"]

        # Globals
        self.simulation = simulation
        self.events_manager: desym.timed_events_manager.TimedEventsManager = (
            self.simulation.events_manager
        )
        self.origin: desym.objects.stopper.core.Stopper
        self.destiny: desym.objects.stopper.core.Stopper

        # Container storage pointer
        self.container: Container | None = None

        # DEVS states and events
        self.input_events: events.InputEvents = events.InputEvents(self)
        self.output_events: events.OutputEvents = events.OutputEvents(self)
        self.states: states.State = states.State(self)

    def __str__(self) -> str:
        return f"Conveyor {self.id}"

    def set_origin(self, origin: desym.objects.stopper.core.Stopper) -> None:
        self.origin = origin

    def set_destiny(self, destiny: desym.objects.stopper.core.Stopper) -> None:
        self.destiny = destiny
