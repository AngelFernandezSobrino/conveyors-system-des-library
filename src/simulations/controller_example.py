from simulator import BehaviourController
import simulator.behaviour_controller
from simulator.objects import Stopper, Tray, Product

n = 0


class BehaviourControllerExample(BehaviourController):
    def __init__(self, system_description: dict):
        super().__init__(system_description)

        self.external_functions = {
            0: external_input
        }

        self.check_request_functions = {
            '1': [delay, {'time': 10}],
            '2': [delay, {'time': 5}]
        }

        self.return_rest_functions = {
            '0': external_input
        }


def delay(params, data: simulator.behaviour_controller.CheckRequestData):
    stopper = data['simulation'][data['stopper_id']]
    stopper.lock(stopper.output_ids[0])
    if stopper.request_time == params['time']:
        data['events_register'].push(stopper.unlock, stopper.output_ids[0], params['time'])


def load_product(params, data: simulator.behaviour_controller.CheckRequestData):
    stopper = data['simulation'][data['stopper_id']]
    stopper.input_tray.load_product(Product(1, 2))
    data['simulation']['0'].check_request()
    n += 1


def external_input(data: simulator.behaviour_controller.CheckRequestData):
    global n
    if n < 30:
        data['simulation']['0'].input(Tray(n, 2))
        data['simulation']['0'].check_request()
        n += 1
