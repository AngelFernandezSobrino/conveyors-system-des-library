from __future__ import annotations

from pyparsing import C
import desim.events_manager as tem
import sim.results_controller
import sim.item
import desim.objects.container

from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    import desim.objects.stopper
    import desim.core
    from desim.objects.stopper.core import Stopper
    import desim.objects.stopper.states
    from desim.objects.stopper import StopperId
    from desim.objects.container import ContainerId

import logging

logger = logging.getLogger("mains.cont")

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

    def __init__(self, simulation: desim.core.Simulation):
        self.simulation = simulation

        self.results_production = sim.results_controller.CounterController(
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

        # def stopper_logger(context: Stopper):
        #     logger.debug(f"Stopper {context} status change to {context.states.state}")

        # def conveyor_logger(context: desym.objects.conveyor.Conveyor):
        #     logger.debug(f"Conveyor {context} status change to {context.states.state}")

        # for stopper_id, stopper in simulation.stoppers.items():
        #     self.simulation.stopper_external_events_controller.register_event(
        #         stopper_id, tem.CustomEventListener(stopper_logger, (), {})
        #     )

        # for conveyor_id, conveyor in simulation.conveyors.items():
        #     self.simulation.conveyor_external_events_controller.register_event(
        #         conveyor_id, tem.CustomEventListener(conveyor_logger, (), {})
        #     )

        self.stopper_external_functions: dict[
            desim.objects.stopper.StopperId, list[tem.CustomEventListener]
        ] = {
            "DIR04": [
                tem.CustomEventListener(self.delay, (), {"time": 10}),
                tem.CustomEventListener(self.empty_tray),
            ],
            "PT06": [
                tem.CustomEventListener(self.delay, (), {"time": 10}),
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
                tem.CustomEventListener(self.delay, (), {"time": 10}),
                tem.CustomEventListener(self.process_01),
            ],
            "DIR13": [
                tem.CustomEventListener(self.delay, (), {"time": 10}),
                tem.CustomEventListener(self.process_02),
            ],
            "DIR19": [
                tem.CustomEventListener(self.delay, (), {"time": 10}),
                tem.CustomEventListener(self.process_03),
            ],
        }

        for stopper_id, functions in self.stopper_external_functions.items():
            for event in functions:
                self.simulation.stopper_external_events_controller.register_event(
                    stopper_id, event
                )

    def delay(self, stopper: Stopper, time: int = 0):
        if (
            stopper.states.state.node
            != desim.objects.stopper.states.States.Node.OCCUPIED
        ):
            return

        if stopper.container is None:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")

        if self.delay_helper[stopper.id] == stopper.container.id:
            return

        self.delay_helper[stopper.id] = stopper.container.id
        for destiny_stopper_id in stopper.output_conveyors.keys():
            if (
                stopper.states.state.control[destiny_stopper_id]
                != desim.objects.stopper.states.States.Control.LOCKED
            ):
                stopper.input_events.control_lock_by_destiny_id(destiny_stopper_id)
                stopper.timed_events_manager.push(
                    tem.CustomEventListener(
                        callable=stopper.input_events.control_unlock_by_destiny_id,
                        args=(destiny_stopper_id,),
                    ),
                    time,
                )

    def external_container_input(self, context):
        global tray_index
        if tray_index < 15:
            new_tray = desim.objects.container.Container[Product](str(tray_index), None)
            tray_index += 1
            logger.debug(f"External container input {new_tray}")
            self.simulation.containers.append(new_tray)
            self.simulation.stoppers["PT01"].input_events.reserve()
            self.simulation.stoppers["PT01"].input_events.input(new_tray)

    def empty_tray(self, stopper: Stopper[Product]):
        if (
            stopper.states.state.node
            != desim.objects.stopper.states.States.Node.OCCUPIED
        ):
            return

        if not stopper.container:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")
        if stopper.container is None:
            return
        if stopper.container.content is None:
            return
        if stopper.container.content.state != "0":
            return

        if stopper.container.content and stopper.container.content.state == "1":
            logger.debug(f"Emptying {stopper.container} in {stopper}")

            stopper.simulation.events_manager.call(
                "production", stopper.container.content
            )
            stopper.container.content = None

    def fill_tray_one_product(self, stopper: Stopper[Product]):
        if (
            stopper.states.state.node
            != desim.objects.stopper.states.States.Node.OCCUPIED
        ):
            return

        if not stopper.container:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")
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

    def fill_tray_three_products(self, stopper: Stopper[Product]):
        if (
            stopper.states.state.node
            != desim.objects.stopper.states.States.Node.OCCUPIED
        ):
            return

        if not stopper.container:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")

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

    def process_01(self, stopper: Stopper[Product]):
        if (
            stopper.states.state.node
            != desim.objects.stopper.states.States.Node.OCCUPIED
        ):
            return

        if not stopper.container:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")
        if not (stopper.container and stopper.container.content):
            return

        if (
            stopper.container.content.item_type == ProductTypeReferences.product_1
            and stopper.container.content.state == "0"
        ):
            logger.debug(f"Process 01: Processing {stopper.container} in {stopper}")
            stopper.container.content.update_state("1")

    def process_02(self, stopper: Stopper[Product]):
        if (
            stopper.states.state.node
            != desim.objects.stopper.states.States.Node.OCCUPIED
        ):
            return

        if not stopper.container:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")
        if (
            stopper.container
            and stopper.container.content
            and stopper.container.content.item_type == ProductTypeReferences.product_2
            and stopper.container.content.state == "0"
        ):
            logger.debug(f"Process 02: Processing {stopper.container} in {stopper}")
            stopper.container.content.update_state("1")

    def process_03(self, stopper: Stopper[Product]):
        if (
            stopper.states.state.node
            != desim.objects.stopper.states.States.Node.OCCUPIED
        ):
            return

        if not stopper.container:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")
        if (
            stopper.container
            and stopper.container.content
            and stopper.container.content.item_type == ProductTypeReferences.product_3
            and stopper.container.content.state == "0"
        ):
            logger.debug(f"Process 03: Processing {stopper.container} in {stopper}")
            stopper.container.content.update_state("1")

    def bifurcation_pt05(self, stopper: Stopper[Product]):
        logger.debug(f"Bifurcation PT05: {stopper.states.state}")
        if (
            stopper.states.state.node
            != desim.objects.stopper.states.States.Node.OCCUPIED
        ):
            return

        if not stopper.container:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")

        if stopper.container.content:
            logger.debug(f"Bifurcation PT05: Moving {stopper.container} to DIR08")
            if (
                stopper.states.state.control["DIR05"]
                != desim.objects.stopper.states.States.Control.LOCKED
            ):
                stopper.input_events.control_lock_by_destiny_id("DIR05")

            if (
                stopper.states.state.control["DIR08"]
                != desim.objects.stopper.states.States.Control.UNLOCKED
            ):
                stopper.input_events.control_unlock_by_destiny_id(None, "DIR08")
        else:
            logger.debug(f"Bifurcation PT05: Moving {stopper.container} to DIR05")

            if (
                stopper.states.state.control["DIR05"]
                != desim.objects.stopper.states.States.Control.UNLOCKED
            ):
                stopper.input_events.control_unlock_by_destiny_id(None, "DIR05")

            if (
                stopper.states.state.control["DIR08"]
                != desim.objects.stopper.states.States.Control.LOCKED
            ):
                stopper.input_events.control_lock_by_destiny_id("DIR08")

    def bifurcation_pt09(self, stopper: Stopper[Product]):
        if (
            stopper.states.state.node
            != desim.objects.stopper.states.States.Node.OCCUPIED
        ):
            return

        if not stopper.container:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")
        if (
            stopper.container
            and stopper.container.content
            and stopper.container.content.item_type == ProductTypeReferences.product_1
            and stopper.container.content.state == "0"
        ):
            logger.debug(f"Bifurcation PT09: Moving {stopper.container} to DIR11")
            stopper.input_events.control_lock_by_destiny_id("DIR11")
            stopper.input_events.control_unlock_by_destiny_id(None, "DIR14")
        else:
            logger.debug(f"Bifurcation PT09: Moving {stopper.container} to DIR14")
            stopper.input_events.control_lock_by_destiny_id("DIR14")
            stopper.input_events.control_unlock_by_destiny_id(None, "DIR11")

    def bifurcation_pt10(self, stopper: Stopper[Product]):
        if (
            stopper.states.state.node
            != desim.objects.stopper.states.States.Node.OCCUPIED
        ):
            return

        if not stopper.container:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")
        if (
            stopper.container
            and stopper.container.content
            and stopper.container.content.item_type == ProductTypeReferences.product_3
            and stopper.container.content.state == "0"
        ):
            logger.debug(f"Bifurcation PT10: Moving {stopper.container} to DIR15")
            stopper.input_events.control_lock_by_destiny_id("DIR13")
            stopper.input_events.control_unlock_by_destiny_id(None, "DIR15")
        else:
            logger.debug(f"Bifurcation PT10: Moving {stopper.container} to DIR13")
            stopper.input_events.control_lock_by_destiny_id("DIR15")
            stopper.input_events.control_unlock_by_destiny_id(None, "DIR13")

    def bifurcation_pt16(self, stopper: Stopper[Product]):
        if (
            stopper.states.state.node
            != desim.objects.stopper.states.States.Node.OCCUPIED
        ):
            return

        if not stopper.container:
            raise Exception(f"Fatal error: Tray is None, WTF {stopper.container}")
        if not stopper.container:
            return

        if not stopper.container.content or stopper.container.content.state == "1":
            logger.debug(f"Bifurcation PT16: Moving {stopper.container} to DIR07")
            stopper.input_events.control_lock_by_destiny_id("PT17")
            stopper.input_events.control_unlock_by_destiny_id(None, "DIR07")
        else:
            logger.debug(f"Bifurcation PT16: Moving {stopper.container} to DIR07")
            stopper.input_events.control_lock_by_destiny_id("DIR07")
            stopper.input_events.control_unlock_by_destiny_id(None, "PT17")
