from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import desim.core
    import sim.controller

from sim import item

action_to_product_type_table = {
    0: item.ProductTypeReferences.product_1,
    1: item.ProductTypeReferences.product_2,
    2: item.ProductTypeReferences.product_3,
}


def action_to_product_type(action):
    return action_to_product_type_table[action]


def observation_from_simulator(simulator: desim.core.Simulation[item.Product]):
    return {
        "conveyors": [
            conveyors.s.state.state.value for conveyors in simulator.conveyors.values()
        ],
        "stoppers": [
            stopper.s.state.node.value for stopper in simulator.stoppers.values()
        ],
    }


def reward_from_simulator(controller: sim.controller.SimulationController):
    return (
        controller.results_production.counters[item.ProductTypeReferences.product_1]
        + controller.results_production.counters[item.ProductTypeReferences.product_2]
    )
