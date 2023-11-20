from typing import TYPE_CHECKING, Dict

import tests.sim.settings as settings
from tests.sim.logger import logger

import desym.core

if TYPE_CHECKING:
    from tests.sim.item import Product

from math import fsum
import time

time_one = time.time()
time_two = time.time()

sim_time_max: float = 0
sim_time_min: float = 20

callback_time_max: float = 0
callback_time_min: float = 20

sim_time_list: list[float] = []
callback_time_list: list[float] = []

calc_mean_interval = 0

lines_to_delete = 0


def check_simulation_errors(core: desym.core.Simulation):
    # Loop over all stopper objects and check if any tray is located at two places at the same time
    tray_locations: Dict[str, list[str]] = {}
    for stopper in core.stoppers.values():
        if stopper.input_tray:
            if stopper.input_tray.id in tray_locations:
                tray_locations[stopper.input_tray.id].append(
                    stopper.stopper_id + " input"
                )
            else:
                tray_locations[stopper.input_tray.id] = [
                    stopper.stopper_id + " input"
                ]
        output = 0
        for tray in stopper.output_trays.values():
            if tray:
                if tray.id in tray_locations:
                    tray_locations[tray.id].append(
                        stopper.stopper_id + f" output {output}"
                    )
                else:
                    tray_locations[tray.id] = [
                        stopper.stopper_id + f" output {output}"
                    ]
            output += 1

    # for i in range(len(tray_locations)):
    #     tray_string += (
    #         f"Tray {i} { [stopper_id for stopper_id in tray_locations[str(i)]] } \n "
    #     )
    #     next_lines_to_delete += 1

    for tray_id in tray_locations:
        if len(tray_locations[tray_id]) > 1:
            logger.error(f"Tray {tray_id} is located at {tray_locations[tray_id]}")
            raise Exception(f"Tray {tray_id} is located at {tray_locations[tray_id]}")

    # Check if all trays in simulation are located at some stopper
    for tray in core.containers:
        if tray.id not in tray_locations:
            logger.error(f"Tray {tray} is not located at any stopper")
            raise Exception(f"Tray {tray} is not located at any stopper")

    # Check if all trays have different items
    tray_items: Dict[str, list[Product]] = {}
    for tray in core.containers:
        if not tray.content:
            break
        if tray.id in tray_items:
            tray_items[tray.id].append(tray.content)
        else:
            tray_items[tray.id] = [tray.content]

    for tray_id in tray_items:
        if len(tray_items[tray_id]) > 1:
            logger.error(f"Tray {tray_id} has items {tray_items[tray_id]}")
            raise Exception(f"Tray {tray_id} has items {tray_items[tray_id]}")


def print_simulation_data(core: desym.core.Simulation):
    global lines_to_delete
    next_lines_to_delete = 2
    tray_string = ""
    for stopper in core.stoppers.values():
        tray_string += f"Stopper {stopper.stopper_id} input: {stopper.input_tray.id if stopper.input_tray is not None else None } { [tray.id if tray is not None else None for tray in stopper.output_trays.values()]} \n "
        next_lines_to_delete += 1
    global sim_time_max, sim_time_min, callback_time_max, callback_time_min, calc_mean_interval
    sim_time = (time_one - time_two) * 1000
    callback_time = (time.time() - time_one) * 1000
    if sim_time > sim_time_max:
        sim_time_max = sim_time
    if sim_time < sim_time_min:
        sim_time_min = sim_time
    if callback_time > callback_time_max:
        callback_time_max = callback_time
    if callback_time < callback_time_min:
        callback_time_min = callback_time

    if calc_mean_interval == 10:
        sim_time_list.append(sim_time)
        callback_time_list.append(callback_time)
        calc_mean_interval = 0

    calc_mean_interval += 1

    sim_time_mean = 0
    callback_time_mean = 0

    # Calculate mean values
    if len(sim_time_list) > 100:
        sim_time_list.pop(0)
        callback_time_list.pop(0)
    if len(sim_time_list) > 0:
        sim_time_mean = sum(sim_time_list) / len(sim_time_list)  # type: ignore
        callback_time_mean = sum(callback_time_list) / len(callback_time_list)  # type: ignore
    for i in range(lines_to_delete):
        LINE_UP = "\033[1A"
        LINE_CLEAR = "\x1b[2K"
        print(LINE_UP, end=LINE_CLEAR)

    lines_to_delete = next_lines_to_delete
    print(
        f"Step:{core.events_manager.step} Sim time:"
        + "{:4.4f}".format(sim_time)
        + " Max: "
        + "{:4.4f}".format(sim_time_max)
        + " Min: "
        + "{:4.4f}".format(sim_time_min)
        + " Mean: "
        + "{:4.4f}".format(sim_time_mean)
        + " Callback time:"
        + "{:4.4f}".format(callback_time)
        + " Max: "
        + "{:4.4f}".format(callback_time_max)
        + " Min: "
        + "{:4.4f}".format(callback_time_min)
        + " Mean: "
        + "{:4.4f}".format(callback_time_mean)
        + f" \n {tray_string}"
    )
