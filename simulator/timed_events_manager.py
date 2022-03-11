class TimedEventsManager:

    def __init__(self):
        self.events_queue = {}

    def push(self, step, event):
        if step in self.events_queue:
            self.events_queue[step] += [event]
        else:
            self.events_queue[step] = [event]

    def run(self, step):
        events = self.events_queue.pop(step)
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
        event_manager.run(i)
