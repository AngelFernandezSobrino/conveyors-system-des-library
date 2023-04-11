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

        # Tray is in the stopper and waiting for the next step
        self.request = False

        # Tray is moving to the next stopper in destiny
        self.move = {v: False for v in self.c.stopper_description["destiny"]}

        # The path is busy for the tray to move, used by the stopper in the destiny
        self.destiny_not_available = {
            v: False for v in self.c.stopper_description["destiny"]
        }

        # The path is locked by the behaviour controller
        self.management_stop = {
            v: True if self.c.stopper_description["default_locked"] == "True" else False
            for v in self.c.stopper_description["destiny"]
        }

        # The path is locked by other stopper
        # It can be the destiny stopper or another stopper which is using the same destiny

        # That dict is used to check if the destiny is available, it contains one dict for each destiny, and echa one contains the destiny stopper and the branch stoppers that would block the destiny

        self.destiny_not_available_v2: dict[DestinyId, dict[core.StopperId, bool]] = {
            v: {v: False} for v in self.c.stopper_description["destiny"]
        }

    def post_init(self):
        for destiny_id, destiny_stops in self.destiny_not_available_v2.items():
            for input_id in self.c.simulation[
                destiny_id
            ].input_stoppers_ids.values():
                if input_id != self.c.stopper_id:
                    destiny_stops[input_id] = False


    def start_move(self, destiny):
        if (self.c.simulation.stoppers[destiny].check_destiny_available(self.c.stopper_id)):
            raise Exception(f"Destiny not available in the destiny stopper {destiny} for the stopper {self.c.stopper_id}")
        self.request = False
        self.move[destiny] = True
        self.c.output_trays[destiny] = self.c.input_tray
        self.c.input_tray = None
        self.c.events_manager.push(
            Event(self.end_move, tuple(), {"destiny": destiny}), self.c.move_steps[destiny]
        )
        if self.c.default_stopped == 1:
            self.management_stop[destiny] = True
            
        if self.c.move_behaviour[destiny] == 1:
            self.c.events_manager.push(
                self.return_rest, {}, self.c.return_available_steps[destiny]
            )
        if self.c.move_behaviour[destiny] == 0:
            self.return_rest()
        self.c.state_change()

    def end_move(self, destiny: str):
        self.move[destiny] = False
        self.c.output_events.tray_send(destiny)
        if self.c.move_behaviour == 3:
            self.return_rest()
        self.c.state_change()

    def return_rest(self):
        self.available = True
        self.c.process_return_rest()
        self.c.output_events.available_origin()
        self.c.state_change()
    
    def go_request(self):
        self.available = False
        self.request = True
        self.c.output_events.not_available_origin()
        self.c.check_request()
        self.c.state_change()