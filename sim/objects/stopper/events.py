from __future__ import annotations
from typing import TYPE_CHECKING

from sim.objects.tray import Tray

if TYPE_CHECKING:
    from . import core


class InputEvents:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

    # Tray arrival event
    def tray_arrival(self, tray: Tray):
        self.c.input_item = tray
        self.c.tray_arrival_time = self.c.events_register.step
        self.c.states.go_request()

    # Externl event to stop tray movement from behaviour controller
    def lock(self, output_ids: list[str] = [], all: bool = False):
        for output_id in output_ids:
            self.c.states.management_stop[output_id] = True

    def unlock(self, output_ids: list[str] = [], all: bool = False):
        for output_id in output_ids:
            self.c.states.management_stop[output_id] = False
        self.c.check_request()

    # System event to stop tray movement from other stoppers
    def not_available(self, output_id, cause_id):
        self.c.states.destiny_not_available_v2[output_id][cause_id] = True

    def available(self, output_id, cause_id):
        self.c.states.destiny_not_available_v2[output_id][cause_id] = False
        self.c.check_request()


class OutputEvents:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

    def tray_send(self, destiny):
        output_object = self.c.output_items[destiny]
        self.c.output_items[destiny] = False
        self.c.simulation[destiny].input_events.tray_arrival(output_object)

    def not_available_origin(self):
        for origin in self.c.input_stoppers_ids:
            self.c.simulation[origin].input_events.not_available(
                self.c.stopper_id, self.c.stopper_id
            )

    def available_origin(self):
        for origin in self.input_ids:
            self.c.simulation[origin].input_events.available(
                self.c.stopper_id, self.c.stopper_id
            )

    def not_available_branch(self, destiny):
        for in_branch_stopper_id in self.c.states.destiny_not_available_v2[
            destiny
        ].keys():
            if in_branch_stopper_id == destiny:
                continue
            self.c.simulation[in_branch_stopper_id].input_events.not_available(
                destiny, self.c.stopper_id
            )

    def available_branch(self, destiny):
        for in_branch_stopper_id in self.c.states.destiny_not_available_v2[
            destiny
        ].keys():
            if in_branch_stopper_id == destiny:
                continue
            self.c.simulation[in_branch_stopper_id].input_events.available(
                destiny, self.c.stopper_id
            )
