class TimedEventsManager:

    def __init__(self):
        self.events_queue = {}
        self.step = -1

    def push(self, event, args, step_delta):
        step = self.step + step_delta
        if step in self.events_queue:
            self.events_queue[step] += [[event, args]]
        else:
            self.events_queue[step] = [[event, args]]

    def add(self, event, args, step):
        if step in self.events_queue:
            self.events_queue[step] += [[event, args]]
        else:
            self.events_queue[step] = [[event, args]]

    def run(self):
        self.step += 1
        if self.step not in self.events_queue:
            return
        events = self.events_queue.pop(self.step)
        for event in events:
            event[0](event[1])


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
