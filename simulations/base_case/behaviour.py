import simulator
from simulator.objects import Stopper, Tray, Product

n = 0


class BehaviourControllerBaseline(simulator.BehaviourController):
    def __init__(self, system_description: dict):
        super().__init__(system_description)

        self.external_functions = {
            0: external_input
        }

        self.check_request_functions = {
            '1': [simulator.behaviour_controller.delay, {'time': 10}],
            '2': [simulator.behaviour_controller.delay, {'time': 5}]
        }

        self.return_rest_functions = {
            '0': external_input
        }


def load_product(params, data: simulator.behaviour_controller.CheckRequestData):
    stopper = data['stopper']
    stopper.input_tray.load_product(Product(1, 2))
    data['simulation']['0'].check_request()
    n += 1


def external_input(data: simulator.behaviour_controller.CheckRequestData):
    global n
    if n < 30:
        data['simulation']['0'].input(Tray(n, 2))
        data['simulation']['0'].check_request()
        n += 1
