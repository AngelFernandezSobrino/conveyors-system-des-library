from __future__ import annotations
from typing import TYPE_CHECKING
from desym.helpers.timed_events_manager import Event


if TYPE_CHECKING:
    from . import core
    from .core import Stopper

DestinyId = str

# Stopper states class, implement the stopper state machine
## States:
# Available: The stopper is available to receive trays
# Reserved: The stopper is reserved to receive a tray
# Request: The stopper has a tray and is waiting for a destiny to be available
# Move: The stopper is moving a tray to a destiny


class State:
    def __init__(self, core: core.Stopper) -> None:
        self.c = core

        self.available = True
        self.reserved = False
        self.request = False
        self.move = {v: False for v in self.c.stopper_description["destiny"]}

        # The path is locked by the behavior controller
        self.management_stop = {
            destiny: True
            if self.c.stopper_description["default_locked"] == "True"
            else False
            for destiny in self.c.stopper_description["destiny"]
        }

        self.graph_stop = {
            destiny: False for destiny in self.c.stopper_description["destiny"]
        }

    def go_move(self, destiny: Stopper.StopperId) -> None:
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
            self.c.behaviorInfo.move_steps[destiny],
        )

        if self.c.behaviorInfo.default_stopped == 1:
            self.management_stop[destiny] = True

        if self.c.behaviorInfo.move_behaviour[destiny] == 1:
            self.c.events_manager.push(
                Event(self.go_available, tuple(), {}),
                self.c.behaviorInfo.return_available_steps[destiny],
            )
        if self.c.behaviorInfo.move_behaviour[destiny] == 0:
            self.go_available()
        self.c._state_change()

    def end_move(self, destiny: str) -> None:
        self.move[destiny] = False
        self.c.output_events.tray_send(destiny)
        if self.c.behaviorInfo.move_behaviour == 3:
            self.go_available()
        self.c._state_change()

    def go_available(self) -> None:
        self.available = True
        self.c._process_return_rest()
        self.c.output_events.available_origins()
        self.c._state_change()

    def go_reserved(self) -> None:
        self.available = False
        self.reserved = True
        self.c._state_change()

    def go_request(self) -> None:
        self.reserved = False
        self.request = True
        self.c._check_request()
        self.c._state_change()
