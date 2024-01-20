from __future__ import annotations
from typing import (
    Callable,
    Dict,
    Mapping,
    TypedDict,
    TYPE_CHECKING,
    TypeVar,
    Generic,
    List,
)

import time

from desym.helpers.timed_events_manager import Event, TimedEventsManager
from desym.objects.stopper.core import Stopper
from desym.objects.container import Container

if TYPE_CHECKING:
    import desym.objects.system

import desym.controllers.results_controller
import desym.controllers.behavior_controller

import logging

logger = logging.getLogger("desym.core")
logFormatter = logging.Formatter(fmt="%(name)s: %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


BehaviorControllerType = TypeVar(
    "BehaviorControllerType",
    bound=desym.controllers.behavior_controller.BaseBehaviourController,
)

ResultsControllerType = TypeVar(
    "ResultsControllerType",
    bound=desym.controllers.results_controller.BaseResultsController,
)


class Simulation(Generic[BehaviorControllerType, ResultsControllerType]):
    def __init__(
        self,
        description: desym.objects.system.SystemDescription,
        behavior_controllers: Mapping[str, BehaviorControllerType],
        results_controllers: Mapping[str, ResultsControllerType],
        callback_after_step_event: Callable[[Simulation], None] | None,
    ) -> None:
        
        self.events_manager = TimedEventsManager()
        
        self.description = description
        self.behavior_controllers = behavior_controllers
        self.results_controllers = results_controllers

        self.callback_after_step_event = callback_after_step_event
        for behavior_controller in behavior_controllers.values():
            for (
                step,
                external_function_list,
            ) in behavior_controller.external_functions.items():
                for external_function in external_function_list:
                    self.events_manager.add(
                        Event(external_function, (self,), {}),
                        step,
                    )

        self.stoppers: dict[
            Stopper.StopperId, Stopper[BehaviorControllerType, ResultsControllerType]
        ] = {}
        self.containers: list[Container] = []

        for stopper_id, stopper_description in self.description.items():
            self.stoppers[stopper_id] = Stopper[
                BehaviorControllerType, ResultsControllerType
            ](
                stopper_id,
                stopper_description,
                self,
                behavior_controllers,
                results_controllers,
                False,
            )

        for stopper in self.stoppers.values():
            stopper.post_init()


    def sim_run_real_time_forever(self, real_time_step: float):
        try:
            while True:
                start_time = time.time()
                if self.events_manager.run() and self.callback_after_step_event:
                    self.callback_after_step_event(self)
                
                time.sleep(real_time_step - ((time.time() - start_time) % real_time_step))

        except KeyboardInterrupt:
            res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
            if res == "y":
                return
            else:
                self.sim_run_real_time_forever(real_time_step)

    def sim_run_steps_real_time(self, steps, real_time_step):
        while self.events_manager.step < steps:
            start_time = time.time()
            self.events_manager.run()
            time.sleep(real_time_step - ((time.time() - start_time) % real_time_step))

    def sim_run_steps(self, steps):
        while self.events_manager.step < steps:
            if self.events_manager.run() and self.callback_after_step_event:
                self.callback_after_step_event(self)
