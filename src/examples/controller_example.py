from simulator import BaseBehaviourController
import simulator.controllers.behaviour_controller
from simulator.objects import Tray, Product

n = 0


class BehaviourControllerExample(BaseBehaviourController):
    def __init__(self, system_description: dict):
        super().__init__(system_description)

        self.external_functions = {
            0: external_input
        }

        self.check_request_functions = {
            '1': [simulator.controllers.behaviour_controller.delay, {'time': 10, 'output_index': 0}],
            '2': [simulator.controllers.behaviour_controller.delay, {'time': 5, 'output_index': 0}]
        }

        self.return_rest_functions = {
            '0': external_input
        }


def load_product(params, data: simulator.controllers.behaviour_controller.CheckRequestData):
    stopper = data['simulation'][data['stopper_id']]
    stopper.input_tray.load_product(Product(1, 2))
    data['simulation']['0'].check_request()
    n += 1


def external_input(data: simulator.controllers.behaviour_controller.CheckRequestData):
    global n
    if n < 30:
        data['simulation']['0'].input(Tray(n, 2))
        data['simulation']['0'].check_request()
        n += 1
