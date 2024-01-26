from __future__ import annotations
from typing import Callable, TYPE_CHECKING

import time
from desym.events_manager import EventsManager

from desym.external_function import (
    StopperExternalFunctionController,
)

from desym.events_manager import (
    CustomEventListener,
    Step,
    TimedEventsManager,
)
from desym.objects.conveyor.core import Conveyor, ConveyorDescription
from desym.objects.stopper.core import Stopper
from desym.objects.container import Container

if TYPE_CHECKING:
    import desym.objects.system
    import desym.objects.stopper
    import desym.objects.conveyor


import logging

logger = logging.getLogger("desym.core")
logFormatter = logging.Formatter(fmt="%(name)s: %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


class Simulation:
    def __init__(
        self,
        description: desym.objects.system.SystemDescription,
        stopper_external_events_controller: dict[
            desym.objects.stopper.StopperId, StopperExternalFunctionController
        ],
        system_external_events: dict[Step, list[CustomEventListener]],
        callback_after_step_event: Callable[[Simulation], None] | None,
    ) -> None:
        self.timed_events_manager = TimedEventsManager()

        self.description = description
        self.stopper_external_events_controller = stopper_external_events_controller
        self.system_external_events = system_external_events

        self.events_manager = EventsManager()

        for step, events in self.system_external_events.items():
            for event in events:
                self.events_manager.add(event, step)

        # Build simulation graph

        self.stoppers: dict[desym.objects.stopper.StopperId, Stopper] = {}

        self.conveyors: dict[desym.objects.conveyor.ConveyorId, Conveyor] = {}

        for stopper_id, stopper_description in self.description.items():
            self.stoppers[stopper_id] = Stopper(
                stopper_id,
                stopper_description,
                self,
                self.stopper_external_events_controller[stopper_id],
                False,
            )

        for stopper_id, stopper_description in self.description.items():
            for destiny_stopper_index, destiny_stopper_id in enumerate(
                stopper_description["destiny"]
            ):
                if f"{stopper_id}_{destiny_stopper_id}" not in self.conveyors:
                    self.conveyors["{stopper_id}_{destiny_stopper_id}"] = Conveyor(
                        f"{stopper_id}_{destiny_stopper_id}",
                        ConveyorDescription(
                            origin_id=stopper_id,
                            destiny_id=destiny_stopper_id,
                            steps=stopper_description["steps"][destiny_stopper_index],
                        ),
                        self,
                        False,
                    )

                    self.conveyors["{stopper_id}_{destiny_stopper_id}"].set_origin(
                        self.stoppers[stopper_id]
                    )

                    self.conveyors["{stopper_id}_{destiny_stopper_id}"].set_destiny(
                        self.stoppers[destiny_stopper_id]
                    )

                    self.stoppers[stopper_id].set_output_conveyors(
                        self.conveyors["{stopper_id}_{destiny_stopper_id}"],
                        destiny_stopper_id,
                    )

                    self.stoppers[destiny_stopper_id].set_input_conveyors(
                        self.conveyors["{stopper_id}_{destiny_stopper_id}"], stopper_id
                    )

        # List with all the container in the system
        self.containers: list[Container] = []

    def sim_run_real_time_forever(self, real_time_step: float):
        try:
            while True:
                start_time = time.time()
                if self.timed_events_manager.run() and self.callback_after_step_event:
                    self.callback_after_step_event(self)

                time.sleep(
                    real_time_step - ((time.time() - start_time) % real_time_step)
                )

        except KeyboardInterrupt:
            res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
            if res == "y":
                return
            else:
                self.sim_run_real_time_forever(real_time_step)

    def sim_run_steps_real_time(self, steps, real_time_step):
        while self.timed_events_manager.step < steps:
            start_time = time.time()
            self.timed_events_manager.run()
            time.sleep(real_time_step - ((time.time() - start_time) % real_time_step))

    def sim_run_steps(self, steps):
        while self.timed_events_manager.step < steps:
            if self.timed_events_manager.run() and self.callback_after_step_event:
                self.callback_after_step_event(self)

    def sim_run_forever(self):
        try:
            while True:
                if self.timed_events_manager.run() and self.callback_after_step_event:
                    self.callback_after_step_event(self)
        except KeyboardInterrupt:
            res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
            if res == "y":
                return
            else:
                self.sim_run_forever()
