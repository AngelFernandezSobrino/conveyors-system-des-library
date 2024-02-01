from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, TypedDict, Union

import csv

# Get the actual date and time string for the file name
from datetime import datetime
from desim.objects import stopper
from sim import settings


from sim.item import ProductTypeReferences

if TYPE_CHECKING:
    import desim.core
    import sim.controller


import sim.results_controller


results: Dict[str, Dict] = {}

for product_type in ProductTypeReferences:
    results[f"production.{product_type.name}"] = {0: 0}

results["stoppers_occupied"] = {0: 0}

results["conveyors_moving"] = {0: 0}


def save_actual_results(
    context=None, controller: sim.controller.SimulationController | None = None
) -> None:
    if controller is None:
        return

    for product_type in ProductTypeReferences:
        results[f"production.{product_type.name}"][
            controller.simulation.timed_events_manager.step
        ] = controller.results_production.get(product_type)

    results["stoppers_occupied"][controller.simulation.timed_events_manager.step] = (
        sim.results_controller.calculate_ratio_occupied_stoppers(controller.simulation)
    )

    results["conveyors_moving"][controller.simulation.timed_events_manager.step] = (
        sim.results_controller.calculate_ratio_moving_conveyors(controller.simulation)
    )


def save_data_to_file():

    now = datetime.now()

    # dd/mm/YY H:M:S
    dt_string: str = now.strftime("%Y-%m-%d_%H-%M-%S")

    print("-----------------------------------")
    print("Saving data to file\n")
    print(f"File name: {dt_string}.csv")
    print("Do you want to save data to file? (y/n)")
    input_str = input()
    if input_str != "y":
        print("Are you sure? (y/n)")
        input_str = input()
        if input_str == "y":
            return

    print("Do you want to customize file name? (y/n)")
    input_str = input()
    if input_str == "y":
        print("Enter file name:")
        input_str = input()
        print(input_str)
        print(f"File name: {dt_string}-{input_str}.csv")
        dt_string = f"{dt_string}-{input_str}"

    print("Saving data to file...")

    with open(f"data/simulations/results/{dt_string}.csv", "w") as f:

        writer = csv.writer(f)

        header_row: List[str] = ["step"] + [
            column_name for column_name in results.keys()
        ]

        writer.writerow(header_row)

        for step in results["production.product_1"].keys():
            row: List[Union[int, float]] = [step]

            for column in results.values():
                row.append(column[step])

            writer.writerow(row)
