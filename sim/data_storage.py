from __future__ import annotations

from typing import TYPE_CHECKING

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
