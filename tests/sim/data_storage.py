from __future__ import annotations

from typing import TYPE_CHECKING

from tests.sim.item import ProductTypeReferences

if TYPE_CHECKING:
    import desym.core
    import desym.controllers.results_controller

step_to_time = 0.1
data_dict: dict = {
    "results/busyness": []
}

for index in ProductTypeReferences:
    data_dict[f"results/production/{index.name}"] = []
    
for key in ["DIR04", "PT05", "PT06"]:
    data_dict[f"results/times/{key}"] = []


def production_update_callback(
    controller: desym.controllers.results_controller.CounterResultsController,
    index: ProductTypeReferences,
    step: int,
) -> None:
    data_dict[f"results/production/{index.name}"].append((step, controller.counters[index]))


def time_update_callback(
    results: desym.controllers.results_controller.TimesResultsController, step: int
):
    for key in ["DIR04", "PT05", "PT06"]:
        data_dict[f"results/times/{key}"].append((step, results.accumulated_times[key]))


def busyness_update_callback(controller: desym.controllers.results_controller.TimesResultsController, busyness, step: int):
    data_dict["results/busyness"].append((step, busyness))
