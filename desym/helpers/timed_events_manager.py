from typing import TypedDict, Callable
import typing

Step = int

class Event:
    def __init__(self, callable: typing.Callable, args: tuple, kwargs: dict):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        return self.callable(*self.args, **self.kwargs)


class TimedEventsManager:
    def __init__(self):
        self.events_queue: dict[Step, list[Event]] = {}
        self.step: Step = -1

    # Add a event at "step_delta" steps from current step
    def push(self, event: Event, step_delta: int):
        step = self.step + step_delta
        if step in self.events_queue:
            self.events_queue[step] += [event]
        else:
            self.events_queue[step] = [event]

    # Add a event at the step desired
    def add(self, event: Event, step: int):
        if step in self.events_queue:
            self.events_queue[step] += [event]
        else:
            self.events_queue[step] = [event]

    def run(self):
        self.step += 1
        if self.step not in self.events_queue:
            return
        events = self.events_queue.pop(self.step)
        for event in events:
            event()
