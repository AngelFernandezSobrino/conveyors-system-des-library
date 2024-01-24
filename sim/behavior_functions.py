from typing import TYPE_CHECKING
import typing

from sim.item import Product, ProductTypeReferences

if TYPE_CHECKING:
    from typing import Dict
    from desym.objects.stopper.core import Stopper
    import desym.core

from desym.timed_events_manager import CustomEventListener

import desym.objects.container

import logging

logger = logging.getLogger("main.behaviour")


tray_index = 1
product_type_index: ProductTypeReferences = ProductTypeReferences.product_1

product_serial_number_database: Dict[ProductTypeReferences, int] = {
    ProductTypeReferences.product_1: 1,
    ProductTypeReferences.product_2: 1,
    ProductTypeReferences.product_3: 1,
}


def delay(self: Stopper, time: int = 0):
    for conveyor in self.output_conveyors.values():
        self.input_events.control_lock_by_conveyor_id(conveyor.id)
        self.events_manager.push(
            CustomEventListener(
                callable=self.input_events.control_unlock_by_conveyor_id,
                args=(conveyor.id,),
            ),
            time,
        )


def external_container_input(simulation: desym.core.Simulation):
    global tray_index
    if tray_index < 15:
        new_tray = desym.objects.container.Container[Product](str(tray_index), None)
        tray_index += 1
        simulation.containers.append(new_tray)
        simulation.stoppers["PT01"].input_events.input(new_tray)


def pt01_container_input(stopper: Stopper):
    global tray_index
    if tray_index < 15:
        new_tray = desym.objects.container.Container[Product](str(tray_index), None)
        tray_index += 1
        stopper.simulation.containers.append(new_tray)
        stopper.input_events.input(new_tray)


def calculate_busyness(simulation: desym.core.Simulation):
    if isinstance(simulation.results_controllers["busyness"], TimesResultsController):
        simulation.results_controllers["busyness"].calculate_busyness(
            simulation,
            simulation.events_manager.step,
        )


def empty_tray(stopper: Stopper):
    if stopper.container is None:
        return
    if stopper.container.content is None:
        return
    if stopper.container.content.state != "0":
        return

    if stopper.container.content and stopper.container.content.state == "1":
        logger.debug(f"Emptying {stopper.container} in {stopper}")
        stopper.results_controllers["production"].increment(
            stopper.container.content.item_type, stopper.events_manager.step
        )
        stopper.container.content = None


def fill_tray_one_product(stopper: Stopper):
    global product_serial_number_database
    logger.debug(
        f"Filling {stopper.container} in {stopper} with product id {product_serial_number_database[product_type_index]} of type {product_type_index.name}"
    )
    if not stopper.container:
        return

    if stopper.container.load(
        Product(
            str(product_serial_number_database[product_type_index]),
            ProductTypeReferences.product_1,
            "0",
        )
    ):
        product_serial_number_database[product_type_index] += 1


def fill_tray_three_products(stopper: Stopper):
    global product_type_index, product_serial_number_database
    logger.debug(
        f"Filling {stopper.container} in {stopper} with product id {product_serial_number_database[product_type_index]} of type {product_type_index.name}"
    )
    if not stopper.container:
        return
    if stopper.container.content:
        return

    if product_type_index == ProductTypeReferences.product_1:
        if stopper.container.load(
            Product(
                str(product_serial_number_database[product_type_index]),
                ProductTypeReferences.product_1,
                "0",
            )
        ):
            product_serial_number_database[product_type_index] += 1
        product_type_index = ProductTypeReferences.product_2
    elif product_type_index == ProductTypeReferences.product_2:
        if stopper.container.load(
            Product(
                str(product_serial_number_database[product_type_index]),
                ProductTypeReferences.product_2,
                "0",
            )
        ):
            product_serial_number_database[product_type_index] += 1
        product_type_index = ProductTypeReferences.product_3
    elif product_type_index == ProductTypeReferences.product_3:
        if stopper.container.load(
            Product(
                str(product_serial_number_database[product_type_index]),
                ProductTypeReferences.product_3,
                "0",
            )
        ):
            product_serial_number_database[product_type_index] += 1
        product_type_index = ProductTypeReferences.product_1


def process_01(stopper: Stopper):
    if not (stopper.container and stopper.container.content):
        return

    if (
        stopper.container.content.item_type == ProductTypeReferences.product_1
        and stopper.container.content.state == "0"
    ):
        logger.debug(f"Process 01: Processing {stopper.container} in {stopper}")
        stopper.container.content.update_state("1")


def process_02(stopper: Stopper[Product]):
    if (
        stopper.container
        and stopper.container.content
        and stopper.container.content.item_type == ProductTypeReferences.product_2
        and stopper.container.content.state == "0"
    ):
        logger.debug(f"Process 02: Processing {stopper.container} in {stopper}")
        stopper.container.content.update_state("1")


def process_03(stopper: Stopper[Product]):
    if (
        stopper.container
        and stopper.container.content
        and stopper.container.content.item_type == ProductTypeReferences.product_3
        and stopper.container.content.state == "0"
    ):
        logger.debug(f"Process 03: Processing {stopper.container} in {stopper}")
        stopper.container.content.update_state("1")


def bifurcation_pt05(stopper: Stopper[Product]):
    if not stopper.container:
        return

    if stopper.container.content:
        logger.debug(f"Bifurcation PT05: Moving {stopper.container} to DIR08")
        stopper.input_events.control_lock_by_destiny_id("DIR05")
        stopper.input_events.control_unlock_by_destiny_id("DIR08")
    else:
        logger.debug(f"Bifurcation PT05: Moving {stopper.container} to DIR08")
        stopper.input_events.control_lock_by_destiny_id("DIR08")
        stopper.input_events.control_unlock_by_destiny_id("DIR05")


def bifurcation_pt09(stopper: Stopper[Product]):
    if (
        stopper.container
        and stopper.container.content
        and stopper.container.content.item_type == ProductTypeReferences.product_1
        and stopper.container.content.state == "0"
    ):
        logger.debug(f"Bifurcation PT09: Moving {stopper.container} to DIR11")
        stopper.input_events.control_lock_by_destiny_id("DIR11")
        stopper.input_events.control_unlock_by_destiny_id("DIR14")
    else:
        logger.debug(f"Bifurcation PT09: Moving {stopper.container} to DIR14")
        stopper.input_events.control_lock_by_destiny_id("DIR14")
        stopper.input_events.control_unlock_by_destiny_id("DIR11")


def bifurcation_pt10(stopper: Stopper[Product]):
    if (
        stopper.container
        and stopper.container.content
        and stopper.container.content.item_type == ProductTypeReferences.product_3
        and stopper.container.content.state == "0"
    ):
        logger.debug(f"Bifurcation PT10: Moving {stopper.container} to DIR15")
        stopper.input_events.control_lock_by_destiny_id("DIR13")
        stopper.input_events.control_unlock_by_destiny_id("DIR15")
    else:
        logger.debug(f"Bifurcation PT10: Moving {stopper.container} to DIR13")
        stopper.input_events.control_lock_by_destiny_id("DIR15")
        stopper.input_events.control_unlock_by_destiny_id("DIR13")


def bifurcation_pt16(stopper: Stopper[Product]):
    if not stopper.container:
        return

    if not stopper.container.content or stopper.container.content.state == "1":
        logger.debug(f"Bifurcation PT16: Moving {stopper.container} to DIR07")
        stopper.input_events.control_lock_by_destiny_id("PT17")
        stopper.input_events.control_unlock_by_destiny_id("DIR07")
    else:
        logger.debug(f"Bifurcation PT16: Moving {stopper.container} to DIR07")
        stopper.input_events.control_lock_by_destiny_id("DIR07")
        stopper.input_events.control_unlock_by_destiny_id("PT17")
