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

import logging

logger = logging.getLogger("mains.data_storage")
logFormatter = logging.Formatter("\N{ESC}[0m{name: <30s} - {message}", style="{")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)


results: Dict[str, Dict] = {}

for product_type in ProductTypeReferences:
    results[f"production.{product_type.name}"] = {0: 0}

results["stoppers_occupied"] = {0: 0.0}

results["conveyors_moving"] = {0: 0.0}


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
        sim.results_controller.calculate_ratio_non_rest_stoppers(controller.simulation)
    )

    results["conveyors_moving"][controller.simulation.timed_events_manager.step] = (
        sim.results_controller.calculate_ratio_moving_conveyors(controller.simulation)
    )


def save_data_to_file(save: bool | None = None, name: str | None = None) -> None:

    now = datetime.now()

    # dd/mm/YY H:M:S
    dt_string: str = now.strftime("%Y%m%d%H%M%S")

    print("-----------------------------------")
    print("Fila data storage\n")
    print(f"File name: {dt_string}.csv")
    if save is None:
        print("Do you want to save data to file? (y/n)")
        input_str = input()
        if input_str != "y":
            print("Are you sure? (y/n)")
            input_str = input()
            if input_str == "y":
                return

    if save is False:
        return

    if name is not None:
        if name != "":
            dt_string = f"{dt_string}-{name}"
    else:
        print("Do you want to customize file name? (y/n)")
        input_str = input()
        if input_str == "y":
            print("Enter file name:")
            input_str = input()
            print(input_str)
            print(f"File name: {dt_string}-{input_str}.csv")
            dt_string = f"{dt_string}-{input_str}"

    dt_string = f"{dt_string}-{settings.settings_string()}"

    print("Saving data to file...")

    with open(f"data/simulations/results/{dt_string}.csv", "w") as f:

        writer = csv.writer(f)

        writer.writerow([f"# Settings - STEP_TO_TIME: {settings.STEP_TO_TIME}"])
        writer.writerow([f"# Settings - SIMULATION_TIME: {settings.SIMULATION_TIME}"])
        writer.writerow([f"# Settings - STEPS: {settings.STEPS}"])
        writer.writerow(
            [f"# Settings - MAX_CONTAINERS_AMMOUNT: {settings.MAX_CONTAINERS_AMMOUNT}"]
        )
        writer.writerow(
            [f"#name {' '.join([column_name for column_name in results.keys()])}"]
        )
        writer.writerow(
            [
                f"#datatype {' '.join([str(type(column[0]).__name__) for column in results.values()])}"
            ]
        )

        writer.writerow(["step"] + [column_name for column_name in results.keys()])

        for step in results["production.product_1"].keys():
            row: List[Union[int, float, str]] = [step]

            for column in results.values():
                if isinstance(column[step], float):
                    row.append("%.4f" % column[step])
                else:
                    row.append(column[step])

            writer.writerow(row)

    print("Data correctly saved")


if __name__ == "__main__":
    print("Quick test")
    save_data_to_file()
    pass
