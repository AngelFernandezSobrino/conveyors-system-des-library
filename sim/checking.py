from tkinter import Radiobutton
from typing import TYPE_CHECKING, Set

from sympy import E
import sim

import sim.settings as settings
from sim.logger import logger

import desym.core

if TYPE_CHECKING:
    from sim.item import Product
    import desym.objects.container
    import sim.item

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
    tray_locations: Set[desym.objects.container.ContainerId] = set()
    for stopper in core.stoppers.values():
        if stopper.container:
            if stopper.container.id not in tray_locations:
                tray_locations.add(stopper.container.id)
            else:
                raise Exception(
                    f"Tray {stopper.container.id} is located at two stoppers at the same time"
                )
    for conveyor in core.conveyors.values():
        if conveyor.container:
            if conveyor.container.id not in tray_locations:
                tray_locations.add(conveyor.container.id)
            else:
                raise Exception(
                    f"Tray {conveyor.container.id} is located at two conveyors at the same time"
                )

    # Check if all trays in simulation are located at some stopper
    for tray in core.containers:
        if tray.id not in tray_locations:
            raise Exception(f"Tray {tray} is not located at any stopper")

    # Check if all trays have different items
    tray_items: Set[sim.item.TypeId] = set()
    for tray in core.containers:
        if not tray.content:
            break
        if tray.id not in tray_items:
            tray_items.add(tray.id)
        else:
            raise Exception(f"Tray {tray} has the same item as another tray")


def print_simulation_data(core: desym.core.Simulation):
    global lines_to_delete
    next_lines_to_delete = 2
    tray_string = ""
    for stopper in core.stoppers.values():
        tray_string += f"Stopper {stopper.id} input: {stopper.container.id if stopper.container is not None else None } \n "
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
        f"Step:{core.timed_events_manager.step} Sim time:"
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
