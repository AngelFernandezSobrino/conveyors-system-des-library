from __future__ import annotations
from ast import Return
from typing import (
    Dict,
    Generic,
    TypeVar,
    TypedDict,
    TYPE_CHECKING,
)

from desim.custom_logging import (
    LOGGER_BASE_NAME,
    LOGGER_STOPPER_COLOR,
    LOGGER_STOPPER_NAME,
    get_logger,
)
from desim.objects.container import ContentType

from . import events
from . import states

import desim.objects.stopper

if TYPE_CHECKING:
    from desim.objects.container import Container
    from desim.objects.conveyor.core import Conveyor
    import desim.objects.system
    from desim.external_function import ExternalFunctionController
    from desim.events_manager import TimedEventsManager
    import desim.core
    import desim.objects.stopper
    import desim.objects.conveyor


class StopperDescription(TypedDict):
    destiny: list[desim.objects.stopper.StopperId]
    steps: list[int]
    move_behaviour: list[str]
    rest_steps: list[int]
    default_locked: bool
    priority: int


class Stopper(Generic[ContentType]):
    def __init__(
        self,
        id: desim.objects.stopper.StopperId,
        description: StopperDescription,
        simulation: desim.core.Simulation,
        external_events_controller: ExternalFunctionController,
        debug,
    ):
        self.id = id
        self.description = description
        self.debug = debug
        # External function to emit events to extenal system
        self.external_events_controller = external_events_controller

        self.logger = get_logger(
            f"{LOGGER_BASE_NAME}.{LOGGER_STOPPER_NAME}.{self.id}",
            LOGGER_STOPPER_COLOR + "{name: <30s} - ",
        )

        # Globals
        self.simulation: desim.core.Simulation = simulation
        self.timed_events_manager: TimedEventsManager = (
            self.simulation.timed_events_manager
        )

        self.behaviorInfo = BehaviorInfo(
            id,
            self.description,
            self.simulation.description,
        )

        self.output_conveyors_by_destiny_id: Dict[
            desim.objects.stopper.StopperId, Conveyor
        ] = {}
        self.input_conveyors_by_destiny_id: Dict[
            desim.objects.stopper.StopperId, Conveyor
        ] = {}

        self.input_conveyors_by_conveyor_id: Dict[
            desim.objects.conveyor.ConveyorId, Conveyor
        ] = {}
        self.output_conveyors_by_conveyor_id: Dict[
            desim.objects.conveyor.ConveyorId, Conveyor
        ] = {}

        # Container storage pointer
        self.container: Container[ContentType] | None = None

        # Stopper composition objects
        self.i: events.InputEventsController = events.InputEventsController(self)
        self.o: events.OutputEventsController = events.OutputEventsController(self)
        self.s: states.StateController = states.StateController(self)

    def __str__(self) -> str:
        return f"Stopper {self.id}"

    def set_input_conveyors(
        self,
        input_conveyor: Conveyor,
        origin_stopper_id: desim.objects.stopper.StopperId,
    ) -> None:
        if input_conveyor not in self.input_conveyors_by_destiny_id:
            self.input_conveyors_by_destiny_id[origin_stopper_id] = input_conveyor

        if input_conveyor not in self.input_conveyors_by_conveyor_id:
            self.input_conveyors_by_conveyor_id[input_conveyor.id] = input_conveyor

    def set_output_conveyors(
        self,
        output_conveyor: Conveyor,
        destiny_stopper_id: desim.objects.stopper.StopperId,
    ) -> None:
        if output_conveyor not in self.output_conveyors_by_destiny_id:
            self.output_conveyors_by_destiny_id[destiny_stopper_id] = output_conveyor

        if output_conveyor not in self.output_conveyors_by_conveyor_id:
            self.output_conveyors_by_conveyor_id[output_conveyor.id] = output_conveyor

    def dump(self):
        """
        Return the stopper information and state
        """
        return f"Stopper: {self.id} - {self.s.dump()}"


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
        self.input_stoppers_ids: list[desim.objects.stopper.StopperId] = []
        for external_stopper_id, stopper_info in simulation_description.items():
            if stopper_id in stopper_info["destiny"]:
                self.input_stoppers_ids += [external_stopper_id]
