from __future__ import annotations
from typing import TYPE_CHECKING
from desym.helpers.timed_events_manager import Event


if TYPE_CHECKING:
    from . import core

DestinyId = str


class State:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

        # Available for tray to arrive
        self.available = True

        # Stopper is reserved for a tray to arrive
        self.reserved = False
        # When another stopper send a tray to this stopper, an input event is sent to this stopper to reserve it
        # When the tray arrives the stopper goes to the request state

        # Tray is in the stopper and waiting for the next step
        self.request = False

        # Tray is moving to the next stopper in destiny
        self.move = {v: False for v in self.c.stopper_description["destiny"]}

        # The path is locked by the behaviour controller
        self.management_stop = {
            destiny: True
            if self.c.stopper_description["default_locked"] == "True"
            else False
            for destiny in self.c.stopper_description["destiny"]
        }

        self.destiny_not_available = {
            destiny_id: False for destiny_id in self.c.stopper_description["destiny"]
        }

        # Destinies can be available or not, depending on the destiny stopper state.

    #     self.destiny_not_available_v2: dict[DestinyId, dict[core.StopperId, bool]] = {
    #         destiny_id: {destiny_id: False} for destiny_id in self.c.stopper_description["destiny"]
    #     }

    # def post_init(self):
    #     for destiny_id, destiny_stops in self.destiny_not_available_v2.items():
    #         for input_id in self.c.simulation.stoppers[
    #             destiny_id
    #         ].input_stoppers_ids:
    #             if input_id != self.c.stopper_id:
    #                 destiny_stops[input_id] = False

    def go_move(self, destiny: core.StopperId):
        if not self.c.simulation.stoppers[destiny].its_available():
            raise Exception(
                f"Destiny not available in the destiny stopper {destiny} for the stopper {self.c.stopper_id}"
            )
        self.c.output_events.reserve_destiny(destiny)
        self.request = False
        self.move[destiny] = True
        self.c.output_trays[destiny] = self.c.input_tray
        self.c.input_tray = None
        self.c.events_manager.push(
            Event(self.end_move, tuple(), {"destiny": destiny}),
            self.c.move_steps[destiny],
        )

        if self.c.default_stopped == 1:
            self.management_stop[destiny] = True

        if self.c.move_behaviour[destiny] == 1:
            self.c.events_manager.push(
                self.go_rest, {}, self.c.return_available_steps[destiny]
            )
        if self.c.move_behaviour[destiny] == 0:
            self.go_rest()
        self.c._state_change()

    def end_move(self, destiny: str):
        self.move[destiny] = False
        self.c.output_events.tray_send(destiny)
        if self.c.move_behaviour == 3:
            self.go_rest()
        self.c._state_change()

    def go_rest(self):
        self.available = True
        self.c._process_return_rest()
        self.c.output_events.available_origins()
        self.c._state_change()

    def go_reserved(self):
        self.available = False
        self.reserved = True
        self.c._state_change()

    def go_request(self):
        self.reserved = False
        self.request = True
        self.c._check_request()
        self.c._state_change()
