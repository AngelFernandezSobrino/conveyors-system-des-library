
from simulator import ControllerBase
from simulator.objects import Stopper, Tray


class ControllerExample(ControllerBase):
    def __init__(self, system_description: dict):
        super().__init__(system_description)

        self.external = {
            0: external_0
        }

        self.check_request_stopper = {
            '1': check_request_stopper_1,
            '2': check_request_stopper_2
        }


def check_request_stopper_1(simulation_data: dict[str, Stopper]):
    if simulation_data['1'].request_time < 10:
        simulation_data['1'].lock('2')
    else:
        simulation_data['1'].unlock('2')


def check_request_stopper_2(simulation_data: dict[str, Stopper]):
    if simulation_data['2'].request_time < 10:
        simulation_data['2'].lock('3')
    else:
        simulation_data['2'].unlock('3')


def external_0(args):
    args['simulation_data']['0'].input(Tray(23, 2))
