from typing import TypedDict


class Event:
    def __init__(self, callable: callable, args: tuple, kwargs: dict):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        return self.callable(*self.args, **self.kwargs)


class TimedEventsManager:
    def __init__(self):
        self.events_queue: list[list[Event]] = {}
        self.step: int = -1

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


if __name__ == "__main__":
    event_manager = TimedEventsManager()

    class Something:
        def __init__(self):
            self.value = 0

        def event(self):
            self.value += 1
            print(self.value)

    something = Something()

    for i in range(0, 200):
        event_manager.push(i, something.event)

    for i in range(0, 200):
        event_manager.run()
