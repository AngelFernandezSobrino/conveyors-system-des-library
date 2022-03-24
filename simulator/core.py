from timed_events_manager import TimedEventsManager

from stopper import StopperInfo, Stopper


class Core:

    def __init__(self, topology: list[StopperInfo]) -> None:

        self.systemData = []
        self.events_manager = TimedEventsManager()
        self.topology = topology

        for i, stopper in enumerate(topology):
            self.systemData.append(
                Stopper(i, self.topology, self.systemData,
                        self.events_manager))


if __name__ == '__main__':

    topology = [{
        'destiny': [1],
        'steps': [8],
        'behaviour': [1],
        'rest_steps': [1]
    }, {
        'destiny': [2],
        'steps': [8],
        'behaviour': [1],
        'rest_steps': [1]
    }, {
        'destiny': [3],
        'steps': [8],
        'behaviour': [1],
        'rest_steps': [1]
    }, {
        'destiny': [0],
        'steps': [8],
        'behaviour': [1],
        'rest_steps': [1]
    }]

    core = Core(topology)

    print(core.systemData)