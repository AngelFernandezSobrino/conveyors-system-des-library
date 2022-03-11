class EventsManager:

    def __init__(self):
        self.events_queue = {}

    def push(self, step, event, args):
        if step in self.events_queue:
            self.events_queue[step] += [{'event': event, 'args': args}]
        else:
            self.events_queue[step] = [event]

    def run(self):
        for event in self.events_queue:
            event['event'](event['args'])


if __name__ == "__main__":

    event_manager = EventsManager()

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
