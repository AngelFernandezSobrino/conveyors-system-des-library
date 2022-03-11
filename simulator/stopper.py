from timed_events_manager import TimedEventsManager
from tray import Tray

from typing import TypedDict


class StopperInfo(TypedDict):
    destiny: list[int]
    steps: list[int]
    behaviour: list[str]
    rest_steps: list[int]


class Stopper:

    def __init__(self, stopperId: int, topology: list[StopperInfo],
                 systemData: dict, events_register: TimedEventsManager):

        self.stopperId = stopperId
        self.systemData = systemData
        self.topology = topology[stopperId]

        self.outputIds = topology[stopperId]['destiny']

        self.steps = {
            self.outputIds[k]: v
            for k, v in enumerate(self.topology['steps'])
        }
        self.rest_steps = {
            self.outputIds[k]: v
            for k, v in enumerate(self.topology['rest_steps'])
        }
        self.behaviour = {
            self.outputIds[k]: v
            for k, v in enumerate(self.topology['behaviour'])
        }

        self.events_register = events_register

        self.rest = True
        self.request = False
        self.move = {v: False for v in self.topology['destiny']}
        self.stop = {v: False for v in self.topology['destiny']}

        self.inputIds = []

        self.inputTray = False
        self.outputTrays = {v: False for v in self.topology['destiny']}

        for stopperInfo in topology:
            if stopperId in stopperInfo['destiny']:
                self.inputIds += [stopperId]

    def check_request(func):

        def wrapper(self):
            func()
            if not self.request:
                return
            for destiny in self.outputsIds:
                if self.systemData[destiny].check_availability(
                ) and not self.move[destiny] and not self.stop[destiny]:
                    self.start_move(destiny)
                    return

        return wrapper

    def input(self, tray: Tray):
        self.inputTray = tray
        self.rest = False
        self.request = True
        self.check_request()

    def start_move(self, destiny):
        self.move[destiny] = True
        self.outputTrays[destiny] = self.inputTray
        self.inputTray = False
        self.request = False
        self.events_register.push(self.end_move, self.steps[destiny])
        if self.behaviour == 1:
            self.events_register.push(self.return_rest,
                                      self.rest_steps[destiny])

    def return_rest(self):
        self.rest = True

    @check_request
    def end_move(self, destiny):
        self.move[destiny] = False
        self.systemData[destiny].input(self.outputTrays[destiny])
        self.outputTrays[destiny] = False
        if self.behaviour == 0:
            self.return_rest()

    @check_request
    def lock(self, outputId):
        self.stop[outputId] = True

    @check_request
    def unlock(self, outputId):
        self.stop[outputId] = False


if __name__ == '__main__':

    events_manager = TimedEventsManager()

    systemData = []

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

    for i in range(0, 4):
        systemData.append(Stopper(i, topology, systemData, events_manager))
        print(i)
        print(systemData[i])
