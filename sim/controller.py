from __future__ import annotations

import desim.events_manager as tem
import sim.results_controller
import sim.item
import desim.objects.container

import sim.custom_logging as custom_logging

from typing import TYPE_CHECKING, Dict, Literal

if TYPE_CHECKING:
    import desim.objects.stopper
    import desim.core
    from desim.objects.stopper.core import Stopper
    import desim.objects.stopper.states
    from desim.objects.stopper import StopperId
    from desim.objects.container import ContainerId

import logging

logger = custom_logging.get_formated_logger("mains.cont", "{name: <24s} - {message}")

from sim.item import Product, ProductTypeReferences

tray_index = 1
product_type_index: ProductTypeReferences = ProductTypeReferences.product_1

product_serial_number_database: Dict[ProductTypeReferences, int] = {
    ProductTypeReferences.product_1: 1,
    ProductTypeReferences.product_2: 1,
    ProductTypeReferences.product_3: 1,
}


class SimulationController:
    def production_event_listener(self, context: sim.item.Product):
        self.results_production.increment(context.item_type)  # type: ignore

    def __init__(self, simulation: desim.core.Simulation, max_containers_ammount: int):
        self.simulation = simulation
        self.max_containers_ammount = max_containers_ammount

        self.results_production = sim.results_controller.CountersController(
            sim.item.ProductTypeReferences
        )

        self.delay_helper: dict[StopperId, ContainerId] = {
            stopper_id: "" for stopper_id in simulation.stoppers.keys()
        }

        simulation.events_manager.register(
            "production",
            tem.CustomEventListener(self.production_event_listener, (), {}),
        )

        self.results_time = sim.results_controller.CronoController(simulation)

        self.external_container_input_function = tem.CustomEventListener(
            self.external_container_input, (), {}
        )

        self.external_functions = {0: [self.external_container_input_function]}

        self.stopper_external_functions: dict[
            desim.objects.stopper.StopperId, list[tem.CustomEventListener]
        ] = {
            "PT01": [tem.CustomEventListener(self.external_container_input)],
            "DIR04": [
                tem.CustomEventListener(self.delay, (), {"time": 10, "state": "1"}),
                tem.CustomEventListener(self.empty_tray),
            ],
            "PT06": [
                tem.CustomEventListener(
                    self.delay, (), {"time": 10, "no_content": True}
                ),
                tem.CustomEventListener(
                    self.fill_tray_three_products,
                ),
            ],
            "PT05": [
                tem.CustomEventListener(self.bifurcation_pt05),
            ],
            "PT09": [
                tem.CustomEventListener(self.bifurcation_pt09),
            ],
            "PT10": [tem.CustomEventListener(self.bifurcation_pt10)],
            "PT16": [tem.CustomEventListener(self.bifurcation_pt16)],
            "DIR17": [
                tem.CustomEventListener(
                    self.delay,
                    (),
                    {
                        "time": 10,
                        "state": "0",
                        "item_type": ProductTypeReferences.product_1,
                    },
                ),
                tem.CustomEventListener(
                    self.process, (), {"product_type": ProductTypeReferences.product_1}
                ),
            ],
            "DIR13": [
                tem.CustomEventListener(
                    self.delay,
                    (),
                    {
                        "time": 10,
                        "state": "0",
                        "item_type": ProductTypeReferences.product_2,
                    },
                ),
                tem.CustomEventListener(
                    self.process, (), {"product_type": ProductTypeReferences.product_2}
                ),
            ],
            "DIR19": [
                tem.CustomEventListener(
                    self.delay,
                    (),
                    {
                        "time": 10,
                        "state": "0",
                        "item_type": ProductTypeReferences.product_3,
                    },
                ),
                tem.CustomEventListener(
                    self.process, (), {"product_type": ProductTypeReferences.product_3}
                ),
            ],
        }

        for stopper_id, functions in self.stopper_external_functions.items():
            for event in functions:
                self.simulation.stopper_external_events_controller.register_event(
                    stopper_id, event
                )

    def delay(
        self,
        stopper: Stopper,
        time: int = 0,
        no_content: bool = False,
        state: str | None = None,
        item_type: ProductTypeReferences | None = None,
    ):
        container = self.get_valid_occupied_container(stopper)
        if container is None:
            return

        if self.delay_helper[stopper.id] == container.id:
            return

        self.delay_helper[stopper.id] = container.id

        if state is not None:
            product = self.get_container_content_filter(
                container, no_content=no_content, state=state, item_type=item_type
            )

            if product is None:
                return

        for destiny_stopper_id in stopper.output_conveyors.keys():
            if (
                stopper.s.state.control[destiny_stopper_id]
                != desim.objects.stopper.states.StateModel.Control.LOCKED
            ):
                stopper.i.control_lock_by_destiny_id(destiny_stopper_id)
                stopper.timed_events_manager.push(
                    tem.CustomEventListener(
                        callable=stopper.i.control_unlock_by_destiny_id,
                        args=(destiny_stopper_id,),
                    ),
                    time,
                )

    def external_container_input(self, context):
        if (
            self.simulation.stoppers["PT01"].s.state.node
            != desim.objects.stopper.states.StateModel.Node.REST
        ):
            return

        global tray_index
        if len(self.simulation.containers) < self.max_containers_ammount:
            new_tray = desim.objects.container.Container[Product](str(tray_index), None)
            tray_index += 1
            logger.debug(f"External container {new_tray} created")
            self.simulation.containers.append(new_tray)
            logger.debug(f"Reserve PT01 with {new_tray}")
            self.simulation.stoppers["PT01"].i.reserve()
            logger.debug(f"Send to PT01 with {new_tray}")
            self.simulation.stoppers["PT01"].i.receive(new_tray)

    def empty_tray(self, stopper: Stopper[Product]):
        container = self.get_valid_occupied_container(stopper)
        if container is None:
            return
        product = self.get_container_content_filter(container, state="1")

        if product is None:
            return

        logger.debug(f"Emptying {stopper.container} in {stopper}")

        stopper.simulation.events_manager.call("production", product)
        container.content = None

    def fill_tray_one_product(self, stopper: Stopper[Product]):
        container = self.get_valid_occupied_container(stopper)
        if container is None:
            return
        product = self.get_container_content_filter(container, no_content=True)

        if product is not True:
            return

        global product_serial_number_database
        logger.debug(
            f"Filling {stopper.container} in {stopper} with product id {product_serial_number_database[product_type_index]} of type {product_type_index.name}"
        )

        if container.load(
            Product(
                str(product_serial_number_database[product_type_index]),
                ProductTypeReferences.product_1,
                "0",
            )
        ):
            product_serial_number_database[product_type_index] += 1

    def fill_tray_three_products(self, stopper: Stopper[Product]):
        container = self.get_valid_occupied_container(stopper)
        if container is None:
            return
        product = self.get_container_content_filter(container, no_content=True)

        if product is not True:
            return

        global product_type_index, product_serial_number_database
        logger.debug(
            f"Filling {stopper.container} in {stopper} with product id {product_serial_number_database[product_type_index]} of type {product_type_index.name}"
        )

        if product_type_index == ProductTypeReferences.product_1:
            if container.load(
                Product(
                    str(product_serial_number_database[product_type_index]),
                    ProductTypeReferences.product_1,
                    "0",
                )
            ):
                product_serial_number_database[product_type_index] += 1
            product_type_index = ProductTypeReferences.product_2
        elif product_type_index == ProductTypeReferences.product_2:
            if container.load(
                Product(
                    str(product_serial_number_database[product_type_index]),
                    ProductTypeReferences.product_2,
                    "0",
                )
            ):
                product_serial_number_database[product_type_index] += 1
            product_type_index = ProductTypeReferences.product_3
        elif product_type_index == ProductTypeReferences.product_3:
            if container.load(
                Product(
                    str(product_serial_number_database[product_type_index]),
                    ProductTypeReferences.product_3,
                    "0",
                )
            ):
                product_serial_number_database[product_type_index] += 1
            product_type_index = ProductTypeReferences.product_1

    def process(self, stopper: Stopper[Product], product_type: ProductTypeReferences):
        container = self.get_valid_occupied_container(stopper)
        if container is None:
            return
        product = self.get_container_content_filter(
            container, state="0", item_type=product_type
        )

        if isinstance(product, Product):
            logger.debug(
                f"Process {product_type.name}: Processing {stopper.container} in {stopper}"
            )
            product.update_state("1")

    def bifurcation_pt05(self, stopper: Stopper[Product]):
        container = self.get_valid_occupied_container(stopper)
        if container is None:
            return

        logger.debug(f"Bifurcation PT05: {stopper.s.state}")

        if self.get_container_content_filter(container) is not None:
            logger.debug(f"Bifurcation PT05: Moving {stopper.container} to DIR08")
            stopper.i.control_lock_by_destiny_id("DIR05")
            stopper.i.control_unlock_by_destiny_id(None, "DIR08")
            return

        logger.debug(f"Bifurcation PT05: Moving {stopper.container} to DIR05")
        stopper.i.control_unlock_by_destiny_id(None, "DIR05")
        stopper.i.control_lock_by_destiny_id("DIR08")

    def bifurcation_pt09(self, stopper: Stopper[Product]):
        container = self.get_valid_occupied_container(stopper)
        if container is None:
            return
        if (
            self.get_container_content_filter(
                container, state="0", item_type=ProductTypeReferences.product_1
            )
            is not None
        ):
            logger.debug(f"Bifurcation PT09: Moving {stopper.container} to DIR14")
            stopper.i.control_unlock_by_destiny_id(None, "DIR14")
            stopper.i.control_lock_by_destiny_id("DIR11")
            return

        logger.debug(f"Bifurcation PT09: Moving {stopper.container} to DIR11")
        stopper.i.control_unlock_by_destiny_id(None, "DIR11")
        stopper.i.control_lock_by_destiny_id("DIR14")

    def bifurcation_pt10(self, stopper: Stopper[Product]):
        container = self.get_valid_occupied_container(stopper)
        if container is None:
            return
        if (
            self.get_container_content_filter(
                container, state="0", item_type=ProductTypeReferences.product_3
            )
            is not None
        ):
            logger.debug(f"Bifurcation PT10: Moving {stopper.container} to DIR15")
            stopper.i.control_lock_by_destiny_id("DIR13")
            stopper.i.control_unlock_by_destiny_id(None, "DIR15")
            return

        logger.debug(f"Bifurcation PT10: Moving {stopper.container} to DIR13")
        stopper.i.control_lock_by_destiny_id("DIR15")
        stopper.i.control_unlock_by_destiny_id(None, "DIR13")

    def bifurcation_pt16(self, stopper: Stopper[Product]):
        container = self.get_valid_occupied_container(stopper)
        if container is None:
            return

        if self.get_container_content_filter(container, state="1") is not None:
            logger.debug(f"Bifurcation PT16: Moving {stopper.container} to DIR07")
            stopper.i.control_lock_by_destiny_id("PT17")
            stopper.i.control_unlock_by_destiny_id(None, "DIR07")
            return

        logger.debug(f"Bifurcation PT16: Moving {stopper.container} to PT17")
        stopper.i.control_lock_by_destiny_id("DIR07")
        stopper.i.control_unlock_by_destiny_id(None, "PT17")

    def get_container_content_filter(
        self,
        container: desim.objects.container.Container[Product],
        no_content: bool = False,
        state: str | None = None,
        item_type: ProductTypeReferences | None = None,
    ) -> Product | None | Literal[True]:
        if container.content is None:
            if no_content:
                return True
            return None

        if state is not None and container.content.state != state:
            return None

        if item_type is not None and container.content.item_type != item_type:
            return None

        return container.content

    def get_valid_occupied_container(
        self, stopper: Stopper[Product]
    ) -> desim.objects.container.Container[Product] | None:
        if not self.check_stopper_ocuppied(stopper):
            return None

        return self.raise_on_stopper_container_not_present(stopper)

    def check_stopper_ocuppied(self, stopper: Stopper[Product]):
        if (
            stopper.s.state.node
            != desim.objects.stopper.states.StateModel.Node.OCCUPIED
        ):
            return False

        return True

    def raise_on_stopper_container_not_present(
        self, stopper: Stopper[Product]
    ) -> desim.objects.container.Container[Product]:
        if stopper.container is None:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")

        return stopper.container
