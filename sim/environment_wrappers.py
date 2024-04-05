from __future__ import annotations
import bisect
from calendar import c
import collections
from hmac import new
from math import floor
from typing import TYPE_CHECKING

from torch import ne
from desim.objects import conveyor

import numpy as np

if TYPE_CHECKING:
    import desim.core
    import sim.controller

from sim import item

action_to_product_type_table = {
    0: item.ProductTypeReferences.product_1,
    1: item.ProductTypeReferences.product_2,
    2: item.ProductTypeReferences.product_3,
}

product_to_observation_table = {
    item.ProductTypeReferences.product_1: 1,
    item.ProductTypeReferences.product_2: 2,
    item.ProductTypeReferences.product_3: 3,
}


def action_to_product_type(action):
    return action_to_product_type_table[action]


def observation_from_simulator(simulator: desim.core.Simulation[item.Product]):

    stopper_observation = []

    for stopper in simulator.stoppers.values():
        stopper_observation.append(0 if stopper.container is None else 1)
        stopper_observation.append(
            0
            if stopper.container is None or stopper.container.content is None
            else product_to_observation_table[stopper.container.content.item_type]
        )

    conveyor_observation = []

    for conveyor in simulator.conveyors.values():
        conveyor_observation.append(0 if conveyor.container is None else 1)
        conveyor_observation.append(
            0
            if conveyor.container is None or conveyor.container.content is None
            else product_to_observation_table[conveyor.container.content.item_type]
        )

    return np.array([*stopper_observation, *conveyor_observation])


def reward_from_simulator(controller: sim.controller.SimulationControllerBaseline):

    step = controller.simulation.timed_events_manager.step

    data_index = floor(step / 100)

    next_data_index = data_index + 1

    baseline_production = (
        data_table_production[next_data_index] - data_table_production[data_index]
    ) * (step - data_index * 100) / 100 + data_table_production[data_index]

    try:
        return (
            controller.results_production.counters[item.ProductTypeReferences.product_1]
            + controller.results_production.counters[
                item.ProductTypeReferences.product_2
            ]
            + controller.results_production.counters[
                item.ProductTypeReferences.product_3
            ]
            / baseline_production
        )
    except ZeroDivisionError:
        return (
            controller.results_production.counters[item.ProductTypeReferences.product_1]
            + controller.results_production.counters[
                item.ProductTypeReferences.product_2
            ]
            + controller.results_production.counters[
                item.ProductTypeReferences.product_3
            ]
        )


# create a dict from the previous list

data_table_step = [
    0,
    100,
    200,
    300,
    400,
    500,
    600,
    700,
    800,
    900,
    1000,
    1100,
    1200,
    1300,
    1400,
    1500,
    1600,
    1700,
    1800,
    1900,
    2000,
    2100,
    2200,
    2300,
    2400,
    2500,
    2600,
    2700,
    2800,
    2900,
    3000,
    3100,
    3200,
    3300,
    3400,
    3500,
    3600,
    3700,
    3800,
    3900,
    4000,
    4100,
    4200,
    4300,
    4400,
    4500,
    4600,
    4700,
    4800,
    4900,
    5000,
    5100,
    5200,
    5300,
]

data_table_production = [
    0,
    0,
    0,
    0,
    1,
    3,
    5,
    8,
    12,
    17,
    21,
    25,
    29,
    34,
    38,
    42,
    47,
    51,
    55,
    60,
    64,
    68,
    73,
    77,
    81,
    86,
    89,
    94,
    99,
    102,
    107,
    112,
    115,
    120,
    125,
    128,
    133,
    137,
    141,
    146,
    150,
    154,
    159,
    163,
    167,
    172,
    176,
    180,
    185,
    189,
    193,
    197,
    202,
    206,
    210,
    215,
    219,
    223,
    228,
]
