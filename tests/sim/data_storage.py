from __future__ import annotations

import wandb

from typing import TYPE_CHECKING, TypeVar

from tests.sim.item import ProductTypeReferences

if TYPE_CHECKING:
    import desym.core
    import desym.controllers.results_controller
    from desym.core import Simulation

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
    data_dict[f"results/production/{index.name}"] = (step * step_to_time /60, controller.counters[index])


def time_update_callback(
    results: desym.controllers.results_controller.TimesResultsController, step: int
):
    data_dict["results/times"] = {
        key: (step * step_to_time /60, results.times[key]) for key in ["DIR04", "PT05", "PT06"]
    }

def busyness_update_callback(controller: desym.controllers.results_controller.TimesResultsController, busyness, step: int):
    data_dict["results/busyness"] = busyness
