
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import desym.objects.system
    import desym.controllers.results_controller as results_controller

import tests.sim.custom_behaviour as custom_behaviour

step_to_time = 0.25
wandb_data_dict: dict = {}


import wandb

wandb.init(project="i4techlab-simulation", entity="soobbz")
config = wandb.config
wandb.define_metric("results/simulation_time")
wandb.define_metric("results/*", step_metric="results/simulation_time")


def step_callback(core: desym.core.Simulation, enabled: bool):
    if wandb_data_dict != {}:
        wandb_data_dict["results/simulation_time"] = (
            core.events_manager.step * step_to_time / 60
        )
        if enabled:
            wandb.log(wandb_data_dict)
        wandb_data_dict.clear()

def production_update_callback(
    controller: results_controller.CounterResultsController, index, time
):
    wandb_data_dict[f"results/production/{index.name}"] = controller.counters[index]


def time_update_callback(controller: results_controller.TimesResultsController):
    wandb_data_dict["results/times"] = {
        key: controller.times[key] for key in ["DIR04", "PT05", "PT06"]
    }
    wandb_data_dict["results/total_trays"] = custom_behaviour.tray_index


def busyness_update_callback(controller, busyness):
    wandb_data_dict["results/busyness"] = busyness
