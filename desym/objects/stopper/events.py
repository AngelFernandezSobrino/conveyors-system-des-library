from __future__ import annotations
from typing import TYPE_CHECKING

from desym.objects.tray import Tray

if TYPE_CHECKING:
    from . import core

# This classes implement the events connections of the stoppers to other stoppers and to the behaviour controller


class InputEvents:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

    # Event to aknowledge that a tray is being sent to the stopper, used by the stopper to go to reserved state
    def sending_tray(self, origin_id):
        self.c.states.go_reserved()

    # Tray arrival event, used by the stopper to go to request state and manage tray data
    def tray_arrival(self, tray: Tray):
        if self.c.input_tray is not None:
            raise Exception("Input tray is not empty")
        self.c.input_tray = tray
        self.c.tray_arrival_time = self.c.events_manager.step
        self.c.states.go_request()

    # Event to aknowledge that a destiny is becoming available again
    def destiny_available(self, destiny_id):
        if self.c.states.request:
            self.c._check_move()

    # Externl event to stop tray movement from behaviour controller
    def lock(self, output_ids: list[str] = [], all: bool = False):
        if all:
            for output_id in self.c.output_stoppers_ids:
                self.c.states.management_stop[output_id] = True
            return
        for output_id in output_ids:
            self.c.states.management_stop[output_id] = True

    def unlock(self, output_ids: list[str] = [], all: bool = False):
        state_changed = False
        if all:
            for output_id in self.c.output_stoppers_ids:
                if self.c.states.management_stop[output_id]:
                    self.c.states.management_stop[output_id] = False
                    state_changed = True
        else:
            for output_id in output_ids:
                if self.c.states.management_stop[output_id]:
                    self.c.states.management_stop[output_id] = False
                    state_changed = True

        if state_changed:
            self.c._check_move()


# Output events class, used by the stopper to send events to other stoppers
class OutputEvents:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

    # Used to reserve a destiny stopper for a tray to arrive
    def reserve_destiny(self, destiny):
        self.c.simulation.stoppers[destiny].input_events.sending_tray(self.c.stopper_id)

    # Used to send a tray to a destiny stopper
    def tray_send(self, destiny):
        if self.c.output_trays[destiny] is None:
            raise Exception("Output tray is empty")
        output_object = self.c.output_trays[destiny]
        self.c.output_trays[destiny] = None
        self.c.simulation.stoppers[destiny].input_events.tray_arrival(output_object)

    # Used to propagate that the destiny is again available
    def available_origins(self):
        input_ids_array = (
            self.c.input_stoppers_ids
            if self.c.stopper_description["priority"] == 0
            else reversed(self.c.simulation_description["priority"])
        )
        for origin in self.c.input_stoppers_ids:
            self.c.simulation.stoppers[origin].input_events.destiny_available(
                self.c.stopper_id
            )
