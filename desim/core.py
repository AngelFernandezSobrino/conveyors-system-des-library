from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Generic

import time

from desim.events_manager import EventsManager

from desim.external_function import (
    ExternalFunctionController,
)

from desim.events_manager import (
    CustomEventListener,
    Step,
    TimedEventsManager,
)
from desim.objects.conveyor.core import Conveyor, ConveyorDescription
from desim.objects.stopper.core import Stopper
from desim.objects.container import Container

if TYPE_CHECKING:
    import desim.objects.system
    import desim.objects.stopper
    import desim.objects.conveyor
    from typing import Callable

from desim.objects.container import ContentType

import logging

base_logger = logging.getLogger("desim")
logFormatter = logging.Formatter("\N{ESC}[0m{name: <30s} - {message}", style="{")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
base_logger.addHandler(consoleHandler)

base_logger.debug("imported")

logger = logging.getLogger("desim.core")
logger.debug("imported")


class Simulation(Generic[ContentType]):
    def __init__(
        self,
        description: desim.objects.system.SystemDescription,
        debug: bool = False,
    ) -> None:
        if debug:
            logging_level = logging.DEBUG
        else:
            logging_level = logging.INFO

        base_logger.setLevel(logging_level)

        self.timed_events_manager = TimedEventsManager()

        self.description = description

        self.events_manager = EventsManager()

        self.stopper_external_events_controller = ExternalFunctionController()

        self.system_external_events: dict[Step, list[CustomEventListener]] = {}

        self.callback_after_step_event: Callable[[Simulation], None] | None

        self.stop_simulation_signal = False

        # Build simulation graph

        self.stoppers: dict[desim.objects.stopper.StopperId, Stopper[ContentType]] = {}

        self.conveyors: dict[
            desim.objects.conveyor.ConveyorId, Conveyor[ContentType]
        ] = {}

        for stopper_id, stopper_description in self.description.items():
            self.stoppers[stopper_id] = Stopper(
                stopper_id,
                stopper_description,
                self,
                self.stopper_external_events_controller,
                debug=debug,
            )

        for stopper_id, stopper_description in self.description.items():
            for destiny_stopper_index, destiny_stopper_id in enumerate(
                stopper_description["destiny"]
            ):
                if f"{stopper_id}_{destiny_stopper_id}" not in self.conveyors:
                    self.conveyors[f"{stopper_id}_{destiny_stopper_id}"] = Conveyor(
                        f"{stopper_id}_{destiny_stopper_id}",
                        ConveyorDescription(
                            origin_id=stopper_id,
                            destiny_id=destiny_stopper_id,
                            steps=stopper_description["steps"][destiny_stopper_index],
                        ),
                        self,
                        debug=debug,
                    )

                    self.conveyors[f"{stopper_id}_{destiny_stopper_id}"].set_origin(
                        self.stoppers[stopper_id]
                    )

                    self.conveyors[f"{stopper_id}_{destiny_stopper_id}"].set_destiny(
                        self.stoppers[destiny_stopper_id]
                    )

                    self.stoppers[stopper_id].set_output_conveyors(
                        self.conveyors[f"{stopper_id}_{destiny_stopper_id}"],
                        destiny_stopper_id,
                    )

                    self.stoppers[destiny_stopper_id].set_input_conveyors(
                        self.conveyors[f"{stopper_id}_{destiny_stopper_id}"], stopper_id
                    )

        # List with all the container in the system
        self.containers: list[Container] = []

    def register_external_events(
        self, system_external_events: dict[Step, list[CustomEventListener]]
    ):
        self.system_external_events.update(system_external_events)

        for step, events in system_external_events.items():
            for event in events:
                self.timed_events_manager.add(event, step)

    def stop_simulation(self):
        self.stop_simulation_signal = True

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
        while (
            self.timed_events_manager.step < steps and not self.stop_simulation_signal
        ):
            self.timed_events_manager.run()

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

    def dump(self):
        """
        Dump the state of the simulation. Print all stoppers and conveyors states, and all containers in the system, with their respective states and contents.
        """
        result = "Simulation: \n"
        for stopper in self.stoppers.values():
            result += stopper.dump() + "\n"

        for conveyor in self.conveyors.values():
            result += conveyor.dump() + "\n"

        for container in self.containers:
            result += container.dump() + "\n"

        return result
