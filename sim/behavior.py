from enum import Enum
from typing import Dict

from tests.sim.item import Product, ProductTypeReferences

from desym.controllers.behavior_controller import (
    ParametrizedFunction,
    BaseBehaviourController,
    delay,
)
from desym.controllers.results_controller import (
    BaseResultsController,
    CounterResultsController,
    TimesResultsController,
)
from desym.objects.container import Container
from desym.objects.stopper.core import Stopper

import desym.core

import logging

logger = logging.getLogger("main.behaviour")


tray_index = 1
product_type_index: ProductTypeReferences = ProductTypeReferences.product_1

product_serial_number_database: Dict[ProductTypeReferences, int] = {
    ProductTypeReferences.product_1: 1,
    ProductTypeReferences.product_2: 1,
    ProductTypeReferences.product_3: 1,
}


class BaselineBehaviourController(BaseBehaviourController):
    def __init__(self, system_description: dict):
        super().__init__(system_description)

        input_pt01_at_rest_function = ParametrizedFunction(pt01_container_input, {})
        external_container_input_function = ParametrizedFunction(
            external_container_input, {}
        )

        self.external_functions = {0: [external_container_input_function]}

        calculate_busyness_function = ParametrizedFunction(calculate_busyness)

        for i in range(10, 50000, 100):
            self.external_functions[i] = [calculate_busyness_function]

        self.external_functions = {
            "DIR04": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(empty_tray, {}),
            ],
            "PT06": [
                ParametrizedFunction(delay, {"time": 10}),
                ParametrizedFunction(fill_tray_three_products, {}),
            ],
            "PT05": [
                ParametrizedFunction(bifurcation_pt05, {}),
            ],
            "PT09": [
                ParametrizedFunction(bifurcation_pt09, {}),
            ],
            "PT10": [
                ParametrizedFunction(bifurcation_pt10, {}),
            ],
            "PT16": [
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

        self.return_rest_functions = {"PT01": [input_pt01_at_rest_function]}


class CaseStopper(
    Stopper[
        BaselineBehaviourController,
        BaseResultsController | CounterResultsController | TimesResultsController,
    ]
):
    pass


def external_container_input(simulation: desym.core.Simulation, params):
    global tray_index
    if tray_index < 15:
        # logger.debug("New tray entrance at PT01, with id " + str(tray_index))
        logger.debug(f"New tray entrance at PT01, with id {tray_index}")
        new_tray = Container(str(tray_index), None)
        tray_index += 1
        print(type(simulation))
        simulation.containers.append(new_tray)
        simulation.stoppers["PT01"].input_events.arrival(new_tray)


def pt01_container_input(stopper: CaseStopper, params):
    global tray_index
    if tray_index < 15:
        # logger.debug("New tray entrance at PT01, with id " + str(tray_index))
        logger.debug(f"New tray entrance at PT01, with id {tray_index}")
        new_tray = Container(str(tray_index), None)
        tray_index += 1
        stopper.simulation.containers.append(new_tray)
        stopper.input_events.arrival(new_tray)


def calculate_busyness(simulation: desym.core.Simulation, params):
    if isinstance(simulation.results_controllers["busyness"], TimesResultsController):
        simulation.results_controllers["busyness"].calculate_busyness(
            simulation,
            simulation.events_manager.step,
        )


def empty_tray(stopper: Stopper, params):
    if not stopper.input_container:
        return
    if not stopper.input_container.content:
        return
    if not stopper.input_container.content.state:
        return

    if stopper.input_container.content and stopper.input_container.content.state == "1":
        logger.debug(f"Emptying {stopper.input_container} in {stopper}")
        stopper.results_controllers["production"].increment(
            stopper.input_container.content.item_type, stopper.events_manager.step
        )
        stopper.input_container.content = None


def fill_tray_one_product(stopper: Stopper, params):
    global product_serial_number_database
    logger.debug(
        f"Filling {stopper.input_container} in {stopper} with product id {product_serial_number_database[product_type_index]} of type {product_type_index.name}"
    )
    if not stopper.input_container:
        return

    if stopper.input_container.load(
        Product(
            str(product_serial_number_database[product_type_index]),
            ProductTypeReferences.product_1,
            "0",
        )
    ):
        product_serial_number_database[product_type_index] += 1


def fill_tray_three_products(stopper: Stopper, params):
    global product_type_index, product_serial_number_database
    logger.debug(
        f"Filling {stopper.input_container} in {stopper} with product id {product_serial_number_database[product_type_index]} of type {product_type_index.name}"
    )
    if not stopper.input_container:
        return
    if stopper.input_container.content:
        return

    if product_type_index == ProductTypeReferences.product_1:
        if stopper.input_container.load(
            Product(
                str(product_serial_number_database[product_type_index]),
                ProductTypeReferences.product_1,
                "0",
            )
        ):
            product_serial_number_database[product_type_index] += 1
        product_type_index = ProductTypeReferences.product_2
    elif product_type_index == ProductTypeReferences.product_2:
        if stopper.input_container.load(
            Product(
                str(product_serial_number_database[product_type_index]),
                ProductTypeReferences.product_2,
                "0",
            )
        ):
            product_serial_number_database[product_type_index] += 1
        product_type_index = ProductTypeReferences.product_3
    elif product_type_index == ProductTypeReferences.product_3:
        if stopper.input_container.load(
            Product(
                str(product_serial_number_database[product_type_index]),
                ProductTypeReferences.product_3,
                "0",
            )
        ):
            product_serial_number_database[product_type_index] += 1
        product_type_index = ProductTypeReferences.product_1


def process_01(stopper: Stopper, params):
    if not (stopper.input_container and stopper.input_container.content):
        return

    if (
        stopper.input_container.content.item_type == ProductTypeReferences.product_1
        and stopper.input_container.content.state == "0"
    ):
        logger.debug(f"Process 01: Processing {stopper.input_container} in {stopper}")
        stopper.input_container.content.update_state("1")


def process_02(stopper: Stopper, params):
    if (
        stopper.input_container
        and stopper.input_container.content
        and stopper.input_container.content.item_type == ProductTypeReferences.product_2
        and stopper.input_container.content.state == "0"
    ):
        logger.debug(f"Process 02: Processing {stopper.input_container} in {stopper}")
        stopper.input_container.content.update_state("1")


def process_03(stopper: Stopper, params):
    if (
        stopper.input_container
        and stopper.input_container.content
        and stopper.input_container.content.item_type == ProductTypeReferences.product_3
        and stopper.input_container.content.state == "0"
    ):
        logger.debug(f"Process 03: Processing {stopper.input_container} in {stopper}")
        stopper.input_container.content.update_state("1")


def bifurcation_pt05(stopper: Stopper, params):
    if not stopper.input_container:
        return

    if stopper.input_container.content:
        logger.debug(f"Bifurcation PT05: Moving {stopper.input_container} to DIR08")
        stopper.input_events.lock(["DIR05"])
        stopper.input_events.unlock(["DIR08"])
    else:
        logger.debug(f"Bifurcation PT05: Moving {stopper.input_container} to DIR08")
        stopper.input_events.lock(["DIR08"])
        stopper.input_events.unlock(["DIR05"])


def bifurcation_pt09(stopper: Stopper, params):
    if (
        stopper.input_container
        and stopper.input_container.content
        and stopper.input_container.content.item_type == ProductTypeReferences.product_1
        and stopper.input_container.content.state == "0"
    ):
        logger.debug(f"Bifurcation PT09: Moving {stopper.input_container} to DIR11")
        stopper.input_events.lock(["DIR11"])
        stopper.input_events.unlock(["DIR14"])
    else:
        logger.debug(f"Bifurcation PT09: Moving {stopper.input_container} to DIR14")
        stopper.input_events.lock(["DIR14"])
        stopper.input_events.unlock(["DIR11"])


def bifurcation_pt10(stopper: Stopper, params):
    if (
        stopper.input_container
        and stopper.input_container.content
        and stopper.input_container.content.item_type == ProductTypeReferences.product_3
        and stopper.input_container.content.state == "0"
    ):
        logger.debug(f"Bifurcation PT10: Moving {stopper.input_container} to DIR15")
        stopper.input_events.lock(["DIR13"])
        stopper.input_events.unlock(["DIR15"])
    else:
        logger.debug(f"Bifurcation PT10: Moving {stopper.input_container} to DIR13")
        stopper.input_events.lock(["DIR15"])
        stopper.input_events.unlock(["DIR13"])


def bifurcation_pt16(stopper: Stopper, params):
    if not stopper.input_container:
        return

    if (
        not stopper.input_container.content
        or stopper.input_container.content.state == "1"
    ):
        logger.debug(f"Bifurcation PT16: Moving {stopper.input_container} to DIR07")
        stopper.input_events.lock(["PT17"])
        stopper.input_events.unlock(["DIR07"])
    else:
        logger.debug(f"Bifurcation PT16: Moving {stopper.input_container} to DIR07")
        stopper.input_events.lock(["DIR07"])
        stopper.input_events.unlock(["PT17"])
