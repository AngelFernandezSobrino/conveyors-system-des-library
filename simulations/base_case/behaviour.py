from typing import Dict
from enum import Enum

from simulator.controllers import behaviour_controller
from simulator.objects import Tray, Product


class ProductType(Enum):
    product_0 = '0'
    product_1 = '1'
    product_2 = '2'


tray_index = 0
product_type_index: ProductType = ProductType.product_0
product_id_index: Dict[ProductType, int] = {
    ProductType.product_0: 0,
    ProductType.product_1: 0,
    ProductType.product_2: 0
}


class BaselineBehaviourController(behaviour_controller.BaseBehaviourController):
    def __init__(self, system_description: dict):
        super().__init__(system_description)

        self.external_functions = {
            0: external_input
        }

        self.check_request_functions = {
            'DIR04': [
                {
                    'function': behaviour_controller.delay,
                    'params': {'time': 10}
                },
                {
                    'function': empty_tray,
                    'params': {}
                }
            ],
            'PT06': [
                {
                    'function': behaviour_controller.delay,
                    'params': {'time': 10}
                },
                {
                    'function': fill_tray,
                    'params': {}
                }
            ],
            'PT05': [
                {
                    'function': behaviour_controller.delay,
                    'params': {'time': 10}
                },
                {
                    'function': bifurcation_pt05,
                    'params': {}
                }
            ],
            'PT09': [
                {
                    'function': behaviour_controller.delay,
                    'params': {'time': 10}
                },
                {
                    'function': bifurcation_pt09,
                    'params': {}
                }
            ],
            'PT10': [
                {
                    'function': behaviour_controller.delay,
                    'params': {'time': 10}
                },
                {
                    'function': bifurcation_pt10,
                    'params': {}
                }
            ],
            'PT16': [
                {
                    'function': behaviour_controller.delay,
                    'params': {'time': 10}
                },
                {
                    'function': bifurcation_pt16,
                    'params': {}
                }
            ],
            'DIR17': [
                {
                    'function': behaviour_controller.delay,
                    'params': {'time': 10}
                },
                {
                    'function': process_01,
                    'params': {}
                }
            ],
            'DIR13': [
                {
                    'function': behaviour_controller.delay,
                    'params': {'time': 10}
                },
                {
                    'function': process_02,
                    'params': {}
                }
            ],
            'DIR19': [
                {
                    'function': behaviour_controller.delay,
                    'params': {'time': 10}
                },
                {
                    'function': process_03,
                    'params': {}
                }
            ],
        }

        self.return_rest_functions = {
            'PT01': external_input
        }
        for i in range(10, 50000, 100):
            self.external_functions[i] = calculate_busyness


def external_input(data: behaviour_controller.CheckRequestData):
    global tray_index
    if tray_index < 30:
        data['simulation']['PT01'].in_event_input_tray(Tray(tray_index, False))
        tray_index += 1


def calculate_busyness(data: behaviour_controller.CheckRequestData):
    data['simulation']['PT01'].results_controllers[1].calculate_busyness(data['simulation'], data['simulation']['PT01'].events_register.step)


def produce(params, data: behaviour_controller.CheckRequestData):
    if data['stopper'].input_object.product.state == '2':
        data['stopper'].input_object.product.update_state('3')


def empty_tray(params, data: behaviour_controller.CheckRequestData):
    if data['stopper'].input_object.product and data['stopper'].input_object.product.state == '1':
        data['stopper'].results_controllers[0].produce(data['stopper'].input_object.product,
                                                       data['events_register'].step)
        data['stopper'].input_object.product = False


def fill_tray(params, data: behaviour_controller.CheckRequestData):
    if data['stopper'].input_object.product:
        return
    global product_type_index, product_id_index

    if product_type_index == ProductType.product_0:
        data['stopper'].input_object.product = Product(str(product_id_index[ProductType.product_0]),
                                                       ProductType.product_0, '0')
        product_id_index[ProductType.product_0] += 1
        product_type_index = ProductType.product_1
    elif product_type_index == ProductType.product_1:
        data['stopper'].input_object.product = Product(str(product_id_index[ProductType.product_1]),
                                                       ProductType.product_1, '0')
        product_id_index[ProductType.product_1] += 1
        product_type_index = ProductType.product_2
    elif product_type_index == ProductType.product_2:
        data['stopper'].input_object.product = Product(str(product_id_index[ProductType.product_2]),
                                                       ProductType.product_2, '0')
        product_id_index[ProductType.product_2] += 1
        product_type_index = ProductType.product_0


def process_01(params, data: behaviour_controller.CheckRequestData):
    if data['stopper'].input_object.product.model == ProductType.product_0 and \
            data['stopper'].input_object.product.state == '0':
        data['stopper'].input_object.product.update_state('1')


def process_02(params, data: behaviour_controller.CheckRequestData):
    if data['stopper'].input_object.product.model == ProductType.product_1 and \
            data['stopper'].input_object.product.state == '0':
        data['stopper'].input_object.product.update_state('1')


def process_03(params, data: behaviour_controller.CheckRequestData):
    if data['stopper'].input_object.product.model == ProductType.product_2 and \
            data['stopper'].input_object.product.state == '0':
        data['stopper'].input_object.product.update_state('1')


def bifurcation_pt05(params, data: behaviour_controller.CheckRequestData):
    if data['stopper'].input_object.product:
        data['stopper'].in_update_lock({'DIR05': True, 'DIR08': False})
    else:
        data['stopper'].in_update_lock({'DIR05': False, 'DIR08': True})


def bifurcation_pt09(params, data: behaviour_controller.CheckRequestData):
    if data['stopper'].input_object.product.model == ProductType.product_0 and \
            data['stopper'].input_object.product.state == '0':

        data['stopper'].in_update_lock({'DIR14': False, 'DIR11': True})
    else:
        data['stopper'].in_update_lock({'DIR14': True, 'DIR11': False})


def bifurcation_pt10(params, data: behaviour_controller.CheckRequestData):
    if data['stopper'].input_object.product.model == ProductType.product_2 and \
            data['stopper'].input_object.product.state == '0':

        data['stopper'].in_update_lock({'DIR13': True, 'DIR15': False})
    else:
        data['stopper'].in_update_lock({'DIR13': False, 'DIR15': True})


def bifurcation_pt16(params, data: behaviour_controller.CheckRequestData):
    if not data['stopper'].input_object.product or data['stopper'].input_object.product.state == '1':
        data['stopper'].in_update_lock({'DIR07': False, 'PT17': True})
    else:
        data['stopper'].in_update_lock({'DIR07': True, 'PT17': False})
