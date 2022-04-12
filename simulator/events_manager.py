class EventsManager:

    def __init__(self):
        self.events_queue = []

    def push(self, event, args):
        if len(self.events_queue) > 0:
            self.events_queue += [{'event': event, 'args': args}]
        else:
            self.events_queue = [event]

    def run(self):
        while len(self.events_queue) > 0:
            with self.events_queue.pop() as event:
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
