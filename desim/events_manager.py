from __future__ import annotations
from typing import Any, Callable

Step = int
EventName = str


class CustomEventListener:
    def __init__(self, callable: Callable, args: tuple = (), kwargs: dict = {}):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def __call__(self, context: Any = None) -> Any:
        return self.callable(context, *self.args, **self.kwargs)


class TimedEventsManager:
    def __init__(self):
        self.events_queue: dict[Step, list[CustomEventListener]] = {}
        self.step: Step = -1

    # Add a event at "step_delta" steps from current step
    def push(self, event: CustomEventListener, step_delta: int):
        step = self.step + step_delta
        if step in self.events_queue:
            self.events_queue[step] += [event]
        else:
            self.events_queue[step] = [event]

    # Add a event at the step desired
    def add(self, event: CustomEventListener, step: int):
        if step in self.events_queue:
            self.events_queue[step] += [event]
        else:
            self.events_queue[step] = [event]

    def run(self) -> bool:
        self.step += 1
        if self.step not in self.events_queue:
            return False
        events = self.events_queue.pop(self.step)
        for event in events:
            event()
        return True


class EventsManager:
    def __init__(self):
        self.events_callback: dict[EventName, list[Callable]] = {}

    # Add a event at "step_delta" steps from current step
    def register(self, event_name: EventName, event: Callable):
        if event_name in self.events_callback:
            self.events_callback[event_name] += [event]
        else:
            self.events_callback[event_name] = [event]

    def call(self, event_name: EventName, context: Any = None):
        if event_name not in self.events_callback:
            return False
        events = self.events_callback[event_name]
        for event in events:
            event(context)
        return True
