from typing import (
    TypedDict,
    TYPE_CHECKING,
    Union,
)

from . import events
from . import states

if TYPE_CHECKING:
    from desym.objects.container import Container
    from desym.objects.conveyor.core import Conveyor
    import desym.objects.system
    from desym.external_function import StopperExternalFunctionController
    from desym.timed_events_manager import TimedEventsManager
    import desym.core
    import desym.objects.stopper


class StopperDescription(TypedDict):
    destiny: list[desym.objects.stopper.TypeId]
    steps: list[int]
    move_behaviour: list[str]
    rest_steps: list[int]
    default_locked: bool
    priority: int


class Stopper:
    def __init__(
        self,
        id: str,
        description: StopperDescription,
        simulation: desym.core.Simulation,
        external_events_controller: StopperExternalFunctionController,
        debug,
    ):
        self.id = id
        self.description = description

        # External function to emit events to extenal system
        self.external_events_controller = external_events_controller

        # Globals
        self.simulation: desym.core.Simulation = simulation
        self.events_manager: TimedEventsManager = self.simulation.events_manager

        self.behaviorInfo = BehaviorInfo(
            id,
            self.description,
            self.simulation.description,
        )

        self.output_conveyors: list[Conveyor] = []
        self.input_conveyors: list[Conveyor] = []

        # Container storage pointer
        self.container: Container | None = None

        # Request time
        self.input_step = 0

        # Stopper composition objects
        self.input_events: events.InputEvents = events.InputEvents(self)
        self.output_events: events.OutputEvents = events.OutputEvents(self)
        self.states: states.StateController = states.StateController(self)

    def __str__(self) -> str:
        return f"Stopper {self.id}"

    def set_input_conveyors(self, input_conveyor: Conveyor) -> None:
        if input_conveyor not in self.input_conveyors:
            self.input_conveyors.append(input_conveyor)

    def set_output_conveyors(self, output_conveyor: Conveyor) -> None:
        if output_conveyor not in self.output_conveyors:
            self.output_conveyors.append(output_conveyor)


class BehaviorInfo:
    def __init__(self, stopper_id, stopper_description, simulation_description):
        self.default_stopped = stopper_description["default_locked"]
        self.output_stoppers_ids = stopper_description["destiny"]
        self.move_steps = {
            self.output_stoppers_ids[k]: v
            for k, v in enumerate(stopper_description["steps"])
        }
        self.return_available_steps = {
            self.output_stoppers_ids[k]: v
            for k, v in enumerate(stopper_description["rest_steps"])
        }
        self.move_behaviour = {
            self.output_stoppers_ids[k]: v
            for k, v in enumerate(stopper_description["move_behaviour"])
        }
        self.input_stoppers_ids: list[desym.objects.stopper.TypeId] = []
        for external_stopper_id, stopper_info in simulation_description.items():
            if stopper_id in stopper_info["destiny"]:
                self.input_stoppers_ids += [external_stopper_id]
