from typing import Any, TypedDict, Callable
import typing

Step = int


class CustomEventListener:
    def __init__(self, callable: typing.Callable, args: tuple, kwargs: dict):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def __call__(self, context: Any = None):
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
