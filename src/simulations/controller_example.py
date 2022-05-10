
from simulator import BehaviourController
import simulator.behaviour_controller
from simulator.objects import Stopper, Tray


class BehaviourControllerExample(BehaviourController):
    def __init__(self, system_description: dict):
        super().__init__(system_description)

        self.external_functions = {
            0: external_0
        }

        self.check_request_functions = {
            '1': check_request_1,
            '2': check_request_2
        }


def check_request_1(data: simulator.behaviour_controller.CheckRequestData):
    if data['events_register'].step - data['simulation']['1'].request_time < 10:
        data['simulation']['1'].lock('2')
    else:
        data['simulation']['1'].unlock('2')


def check_request_2(data: simulator.behaviour_controller.CheckRequestData):
    if data['events_register'].step - data['simulation']['2'].request_time < 10:
        data['simulation']['2'].lock('3')
    else:
        data['simulation']['2'].unlock('3')


def external_0(args):
    args['simulation_data']['0'].input(Tray(23, 2))
