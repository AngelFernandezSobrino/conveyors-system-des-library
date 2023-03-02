from typing import Dict
from enum import Enum

from sim.controllers.behaviour_controller import (
    ParametrizedFunction,
    BaseBehaviourController,
    delay,
)
from sim.objects import Tray, Item
from sim.objects.stopper.core import Stopper


class ProductType(Enum):
    product_0 = "0"
    product_1 = "1"
    product_2 = "2"


tray_index = 0
product_type_index: ProductType = ProductType.product_0
product_id_index: Dict[ProductType, int] = {
    ProductType.product_0: 0,
    ProductType.product_1: 0,
    ProductType.product_2: 0,
}


class BaselineBehaviourController(BaseBehaviourController):
    def __init__(self, system_description: dict):
        super().__init__(system_description)

        self.external_functions = {0: [ParametrizedFunction(external_input)]}

        for i in range(10, 50000, 100):
            self.external_functions[i] = [ParametrizedFunction(calculate_busyness)]

        self.check_request_functions = {
            "DIR04": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(empty_tray, {}),
            ],
            "PT06": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(fill_tray_three_products, {}),
            ],
            "PT05": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(bifurcation_pt05, {}),
            ],
            "PT09": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(bifurcation_pt09, {}),
            ],
            "PT10": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(bifurcation_pt10, {}),
            ],
            "PT16": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(bifurcation_pt16, {}),
            ],
            # "DIR17": [
            #     ParametrizedFunction(delay, {"time": 10}),
            #     ParametrizedFunction(process_01, {}),
            # ],
            "DIR13": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(process_01, {}),
            ],
            # "DIR19": [
            #     ParametrizedFunction(delay, {"time": 10}),
            #     ParametrizedFunction(process_03, {}),
            # ],
        }

        self.return_rest_functions = {
            # "PT01": [ParametrizedFunction(external_input, {})]
        }


def external_input(self: Stopper, params):
    global tray_index
    if tray_index < 1:
        print("New tray entrance and PT01, with id " + str(tray_index))
        self.simulation.stoppers["PT01"].input_events.tray_arrival(
            Tray(tray_index, False)
        )
        tray_index += 1


def calculate_busyness(self: Stopper, params):
    self.simulation.stoppers["PT01"].results_controllers["busyness"].calculate_busyness(
        self.simulation,
        self.events_manager.step,
    )


def produce(self: Stopper, params):
    if self.input_tray.item.state == "2":
        self.input_tray.item.update_state("3")


def empty_tray(self: Stopper, params):
    if self.input_tray.item and self.input_tray.item.state == "1":
        self.results_controllers["production"].produce(
            self.input_tray.item, self.events_manager.step
        )
        self.input_tray.item = False


def fill_tray_one_product(self: Stopper, params):
    global product_id_index
    if self.input_tray.load_item(
        Item(str(product_id_index), ProductType.product_0, "0")
    ):
        product_id_index += 1


def fill_tray_three_products(self: Stopper, params):
    if self.input_tray.item:
        return
    global product_type_index, product_id_index

    if product_type_index == ProductType.product_0:
        self.input_tray.item = Item(
            str(product_id_index[ProductType.product_0]), ProductType.product_0, "0"
        )
        product_id_index[ProductType.product_0] += 1
        product_type_index = ProductType.product_1
    elif product_type_index == ProductType.product_1:
        self.input_tray.item = Item(
            str(product_id_index[ProductType.product_1]), ProductType.product_1, "0"
        )
        product_id_index[ProductType.product_1] += 1
        product_type_index = ProductType.product_2
    elif product_type_index == ProductType.product_2:
        self.input_tray.item = Item(
            str(product_id_index[ProductType.product_2]), ProductType.product_2, "0"
        )
        product_id_index[ProductType.product_2] += 1
        product_type_index = ProductType.product_0


def process_01(self: Stopper, params):
    if (
        self.input_tray.item.item_type == ProductType.product_0
        and self.input_tray.item.state == "0"
    ):
        self.input_tray.item.update_state("1")


def process_02(self: Stopper, params):
    if (
        self.input_tray.item.item_type == ProductType.product_1
        and self.input_tray.item.state == "0"
    ):
        self.input_tray.item.update_state("1")


def process_03(self: Stopper, params):
    if (
        self.input_tray.item.item_type == ProductType.product_2
        and self.input_tray.item.state == "0"
    ):
        self.input_tray.item.update_state("1")


def bifurcation_pt05(self: Stopper, params):
    if self.input_tray.item:
        self.input_events.lock(["DIR05"])
        self.input_events.unlock(["DIR08"])
    else:
        self.input_events.lock(["DIR08"])
        self.input_events.unlock(["DIR05"])


def bifurcation_pt09(self: Stopper, params):
    if (
        self.input_tray.item.item_type == ProductType.product_0
        and self.input_tray.item.state == "0"
    ):
        self.input_events.lock(["DIR14"])
        self.input_events.unlock(["DIR11"])
    else:
        self.input_events.lock(["DIR11"])
        self.input_events.unlock(["DIR14"])


def bifurcation_pt10(self: Stopper, params):
    if (
        self.input_tray.item.item_type == ProductType.product_2
        and self.input_tray.item.state == "0"
    ):
        self.input_events.lock(["DIR13"])
        self.input_events.unlock(["DIR15"])
    else:
        self.input_events.lock(["DIR15"])
        self.input_events.unlock(["DIR13"])


def bifurcation_pt16(self: Stopper, params):
    if not self.input_tray.item or self.input_tray.item.state == "1":
        self.input_events.lock(["PT17"])
        self.input_events.unlock(["DIR07"])
    else:
        self.input_events.lock(["DIR07"])
        self.input_events.unlock(["PT17"])
