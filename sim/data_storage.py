from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

import csv

# Get the actual date and time string for the file name
from datetime import datetime


from sim.item import ProductTypeReferences

if TYPE_CHECKING:
    import desim.core
    import sim.controller


import sim.results_controller

step_to_time = 0.1
data_dict: dict = {"results/busyness": []}

for index in ProductTypeReferences:
    data_dict[f"results/production/{index.name}"] = []

for key in ["DIR04", "PT05", "PT06"]:
    data_dict[f"results/times/{key}"] = []


def data_storage_update(
    context=None, controller: sim.controller.SimulationController | None = None
) -> None:
    if controller is None:
        return
    for index in ProductTypeReferences:
        data_dict[f"results/production/{index.name}"].append(
            (
                controller.simulation.timed_events_manager.step,
                controller.results_production.counters[index],
            )
        )

    for key in ["DIR04", "PT05", "PT06"]:
        data_dict[f"results/times/{key}"].append(
            (
                controller.simulation.timed_events_manager.step,
                controller.results_time.stoppersResults[key],
            )
        )

    data_dict["results/busyness"].append(
        (
            controller.simulation.timed_events_manager.step,
            sim.results_controller.calculate_busyness(controller.simulation),
        )
    )


def save_data_to_file(settings):

    now = datetime.now()

    # dd/mm/YY H:M:S
    dt_string: str = now.strftime("%d-%m-%Y_%H-%M-%S")

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
        busyness_step = 0
        production_step = {}
        for index in ProductTypeReferences:
            production_step[f"results/production/{index.name}"] = 0

        writer = csv.writer(f)
        writer.writerow(
            ["step", "busyness", "production_1", "production_2", "production_3"]
        )

        for step in range(-1, settings.steps):
            new_row: List[Union[float, None]] = [step]
            write_row = False
            if (
                len(data_dict["results/busyness"]) > busyness_step
                and data_dict["results/busyness"][busyness_step][0] == step
            ):
                # logger.info(f"step: {step}, busyness: {data_storage.data_dict['results/busyness'][busyness_step][1]}")
                new_row.append(data_dict["results/busyness"][busyness_step][1])
                busyness_step += 1
                write_row = True
            else:
                new_row.append(None)

            for index in ProductTypeReferences:
                if (
                    len(data_dict[f"results/production/{index.name}"])
                    > production_step[f"results/production/{index.name}"]
                    and data_dict[f"results/production/{index.name}"][
                        production_step[f"results/production/{index.name}"]
                    ][0]
                    == step
                ):
                    new_row.append(
                        data_dict[f"results/production/{index.name}"][
                            production_step[f"results/production/{index.name}"]
                        ][1]
                    )
                    # logger.info(f"step: {step}, production_1: "+ str(data_storage.data_dict[f"results/production/{index.name}"][production_step[f"results/production/{index.name}"]][1]))

                    production_step[f"results/production/{index.name}"] += 1
                    write_row = True
                else:
                    new_row.append(None)
            if write_row:
                writer.writerow(new_row)
