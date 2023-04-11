from typing import Dict
from enum import Enum

from desym.controllers.behaviour_controller import (
    ParametrizedFunction,
    BaseBehaviourController,
    delay,
)
from desym.controllers.results_controller import (
    BaseResultsController,
    CounterResultsController,
    TimesResultsController,
)
from desym.objects import Tray, Item
from desym.objects.stopper.core import Stopper

import logging

logger = logging.getLogger("main.behaviour")


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

        external_input_function = ParametrizedFunction(external_input, {})

        self.external_functions = {0: [external_input_function]}

        calculate_busyness_function = ParametrizedFunction(calculate_busyness)

        for i in range(10, 50000, 100):
            self.external_functions[i] = [calculate_busyness_function]

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
            "DIR17": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(process_01, {}),
            ],
            "DIR13": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(process_02, {}),
            ],
            "DIR19": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(process_03, {}),
            ],
        }

        self.return_rest_functions = {"PT01": [external_input_function]}


class CaseStopper(
    Stopper[
        BaselineBehaviourController,
        BaseResultsController | CounterResultsController | TimesResultsController,
    ]
):
    pass


def external_input(stopper: CaseStopper, params):
    global tray_index
    if tray_index < 100:
        # logger.debug("New tray entrance at PT01, with id " + str(tray_index))
        logger.debug(f'New tray entrance at PT01, with id {tray_index}')
        new_tray = Tray(str(tray_index), False)
        tray_index += 1
        stopper.simulation.trays.append(new_tray)
        stopper.simulation.stoppers["PT01"].input_events.tray_arrival(new_tray)


def calculate_busyness(stopper: CaseStopper, params):
    stopper.results_controllers["busyness"].calculate_busyness(
        stopper.simulation,
        stopper.events_manager.step,
    )


def empty_tray(stopper: Stopper, params):
    if stopper.input_tray.item and stopper.input_tray.item.state == "1":
        logger.debug(f"Emptying {stopper.input_tray} in {stopper}")
        stopper.results_controllers["production"].increment(
            stopper.input_tray.item.item_type, stopper.events_manager.step
        )
        stopper.input_tray.item = False


def fill_tray_one_product(stopper: Stopper, params):
    global product_id_index
    logger.debug(
        f"Filling {stopper.input_tray} in {stopper} with product id {product_id_index[product_type_index]} of type {product_type_index.name}"
    )
    if stopper.input_tray.load_item(
        Item(str(product_id_index[product_type_index]), ProductType.product_0, "0")
    ):
        product_id_index[product_type_index] += 1


def fill_tray_three_products(stopper: Stopper, params):
    global product_type_index, product_id_index
    logger.debug(
        f"Filling {stopper.input_tray} in {stopper} with product id {product_id_index[product_type_index]} of type {product_type_index.name}"
    )
    if stopper.input_tray.item:
        return

    if product_type_index == ProductType.product_0:
        if stopper.input_tray.load_item(
            Item(str(product_id_index[product_type_index]), ProductType.product_0, "0")
        ):
            product_id_index[product_type_index] += 1
        product_type_index = ProductType.product_1
    elif product_type_index == ProductType.product_1:
        if stopper.input_tray.load_item(
            Item(str(product_id_index[product_type_index]), ProductType.product_1, "0")
        ):
            product_id_index[product_type_index] += 1
        product_type_index = ProductType.product_2
    elif product_type_index == ProductType.product_2:
        if stopper.input_tray.load_item(
            Item(str(product_id_index[product_type_index]), ProductType.product_2, "0")
        ):
            product_id_index[product_type_index] += 1
        product_type_index = ProductType.product_0


def process_01(stopper: Stopper, params):
    if (
        stopper.input_tray
        and stopper.input_tray.item
        and stopper.input_tray.item.item_type == ProductType.product_0
        and stopper.input_tray.item.state == "0"
    ):
        logger.debug(f"Process 01: Processing {stopper.input_tray} in {stopper}")
        stopper.input_tray.item.update_state("1")


def process_02(stopper: Stopper, params):
    if (
        stopper.input_tray
        and stopper.input_tray.item
        and stopper.input_tray.item.item_type == ProductType.product_1
        and stopper.input_tray.item.state == "0"
    ):
        logger.debug(f"Process 02: Processing {stopper.input_tray} in {stopper}")
        stopper.input_tray.item.update_state("1")


def process_03(stopper: Stopper, params):
    if (
        stopper.input_tray
        and stopper.input_tray.item
        and stopper.input_tray.item.item_type == ProductType.product_2
        and stopper.input_tray.item.state == "0"
    ):
        logger.debug(f"Process 03: Processing {stopper.input_tray} in {stopper}")
        stopper.input_tray.item.update_state("1")


def bifurcation_pt05(stopper: Stopper, params):
    if stopper.input_tray.item:
        logger.debug(f"Bifurcation PT05: Moving {stopper.input_tray} to DIR08")
        stopper.input_events.lock(["DIR05"])
        stopper.input_events.unlock(["DIR08"])
    else:
        logger.debug(f"Bifurcation PT05: Moving {stopper.input_tray} to DIR08")
        stopper.input_events.lock(["DIR08"])
        stopper.input_events.unlock(["DIR05"])


def bifurcation_pt09(stopper: Stopper, params):
    if (
        stopper.input_tray
        and stopper.input_tray.item
        and stopper.input_tray.item.item_type == ProductType.product_0
        and stopper.input_tray.item.state == "0"
    ):
        logger.debug(f"Bifurcation PT09: Moving {stopper.input_tray} to DIR11")
        stopper.input_events.lock(["DIR11"])
        stopper.input_events.unlock(["DIR14"])
    else:
        logger.debug(f"Bifurcation PT09: Moving {stopper.input_tray} to DIR14")
        stopper.input_events.lock(["DIR14"])
        stopper.input_events.unlock(["DIR11"])


def bifurcation_pt10(stopper: Stopper, params):
    if (
        stopper.input_tray
        and stopper.input_tray.item
        and stopper.input_tray.item.item_type == ProductType.product_2
        and stopper.input_tray.item.state == "0"
    ):
        logger.debug(f"Bifurcation PT10: Moving {stopper.input_tray} to DIR15")
        stopper.input_events.lock(["DIR13"])
        stopper.input_events.unlock(["DIR15"])
    else:
        logger.debug(f"Bifurcation PT10: Moving {stopper.input_tray} to DIR13")
        stopper.input_events.lock(["DIR15"])
        stopper.input_events.unlock(["DIR13"])


def bifurcation_pt16(stopper: Stopper, params):
    if not stopper.input_tray.item or stopper.input_tray.item.state == "1":
        logger.debug(f"Bifurcation PT16: Moving {stopper.input_tray} to DIR07")
        stopper.input_events.lock(["PT17"])
        stopper.input_events.unlock(["DIR07"])
    else:
        logger.debug(f"Bifurcation PT16: Moving {stopper.input_tray} to DIR07")
        stopper.input_events.lock(["DIR07"])
        stopper.input_events.unlock(["PT17"])
