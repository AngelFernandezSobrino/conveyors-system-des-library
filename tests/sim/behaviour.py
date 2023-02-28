from typing import Dict
from enum import Enum

from sim.controllers import behaviour_controller
from sim.objects import Tray, Item


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


def external_input(checkRequestData: behaviour_controller.CheckRequestData):
    global tray_index
    if tray_index < 10:
        print('New tray entrance and PT01, with id ' + str(tray_index))
        checkRequestData['simulation']['PT01'].input_events.tray_arrival(Tray(tray_index, False))
        tray_index += 1


def calculate_busyness(checkRequestData: behaviour_controller.CheckRequestData):
    checkRequestData['simulation']['PT01'].results_controllers['busyness'].calculate_busyness(checkRequestData['simulation'], checkRequestData['simulation']['PT01'].events_manager.step)


def produce(params, checkRequestData: behaviour_controller.CheckRequestData):
    if checkRequestData['stopper'].input_object.product.state == '2':
        checkRequestData['stopper'].input_object.product.update_state('3')


def empty_tray(params, checkRequestData: behaviour_controller.CheckRequestData):
    if checkRequestData['stopper'].input_object.product and checkRequestData['stopper'].input_object.product.state == '1':
        checkRequestData['stopper'].results_controllers[0].produce(checkRequestData['stopper'].input_object.product,
                                                       checkRequestData['events_register'].step)
        checkRequestData['stopper'].input_object.product = False


def fill_tray(params, checkRequestData: behaviour_controller.CheckRequestData):
    if checkRequestData['stopper'].input_object.product:
        return
    global product_type_index, product_id_index

    if product_type_index == ProductType.product_0:
        checkRequestData['stopper'].input_object.product = Product(str(product_id_index[ProductType.product_0]),
                                                       ProductType.product_0, '0')
        product_id_index[ProductType.product_0] += 1
        product_type_index = ProductType.product_1
    elif product_type_index == ProductType.product_1:
        checkRequestData['stopper'].input_object.product = Product(str(product_id_index[ProductType.product_1]),
                                                       ProductType.product_1, '0')
        product_id_index[ProductType.product_1] += 1
        product_type_index = ProductType.product_2
    elif product_type_index == ProductType.product_2:
        checkRequestData['stopper'].input_object.product = Product(str(product_id_index[ProductType.product_2]),
                                                       ProductType.product_2, '0')
        product_id_index[ProductType.product_2] += 1
        product_type_index = ProductType.product_0


def process_01(params, checkRequestData: behaviour_controller.CheckRequestData):
    if checkRequestData['stopper'].input_object.product.model == ProductType.product_0 and \
            checkRequestData['stopper'].input_object.product.state == '0':
        checkRequestData['stopper'].input_object.product.update_state('1')


def process_02(params, checkRequestData: behaviour_controller.CheckRequestData):
    if checkRequestData['stopper'].input_object.product.model == ProductType.product_1 and \
            checkRequestData['stopper'].input_object.product.state == '0':
        checkRequestData['stopper'].input_object.product.update_state('1')


def process_03(params, checkRequestData: behaviour_controller.CheckRequestData):
    if checkRequestData['stopper'].input_object.product.model == ProductType.product_2 and \
            checkRequestData['stopper'].input_object.product.state == '0':
        checkRequestData['stopper'].input_object.product.update_state('1')


def bifurcation_pt05(params, checkRequestData: behaviour_controller.CheckRequestData):
    if checkRequestData['stopper'].input_object.product:
        checkRequestData['stopper'].in_update_lock({'DIR05': True, 'DIR08': False})
    else:
        checkRequestData['stopper'].in_update_lock({'DIR05': False, 'DIR08': True})


def bifurcation_pt09(params, checkRequestData: behaviour_controller.CheckRequestData):
    if checkRequestData['stopper'].input_object.product.model == ProductType.product_0 and \
            checkRequestData['stopper'].input_object.product.state == '0':

        checkRequestData['stopper'].in_update_lock({'DIR14': False, 'DIR11': True})
    else:
        checkRequestData['stopper'].in_update_lock({'DIR14': True, 'DIR11': False})


def bifurcation_pt10(params, checkRequestData: behaviour_controller.CheckRequestData):
    if checkRequestData['stopper'].input_object.product.model == ProductType.product_2 and \
            checkRequestData['stopper'].input_object.product.state == '0':

        checkRequestData['stopper'].in_update_lock({'DIR13': True, 'DIR15': False})
    else:
        checkRequestData['stopper'].in_update_lock({'DIR13': False, 'DIR15': True})


def bifurcation_pt16(params, checkRequestData: behaviour_controller.CheckRequestData):
    if not checkRequestData['stopper'].input_object.product or checkRequestData['stopper'].input_object.product.state == '1':
        checkRequestData['stopper'].in_update_lock({'DIR07': False, 'PT17': True})
    else:
        checkRequestData['stopper'].in_update_lock({'DIR07': True, 'PT17': False})
