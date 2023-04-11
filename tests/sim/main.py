import pprint
import time
import os
from typing import Dict, TypedDict

import logging

logger = logging.getLogger("main")
logFormatter = logging.Formatter(fmt="%(name)s: %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

logger.setLevel(logging.DEBUG)

import desym.helpers
import desym.core
import desym.controllers.results_controller as results_controller
import desym.controllers.behaviour_controller as behaviour_controller
import behaviour as custom_behaviour

logging.getLogger("desym").setLevel(logging.DEBUG)

config_path = os.path.dirname(os.path.abspath(__file__)) + "/config.xlsx"
config_parser = desym.helpers.ConfigParser(config_path)
config_parser.parse("config_parser")

import wandb

# wandb.init(project="i4techlab-simulation", entity="soobbz")

if not config_parser.config_available:
    raise Exception("Config not available")

# config = wandb.config
# config.data = config_parser.config

# wandb.define_metric("results/simulation_time")
# wandb.define_metric("results/*", step_metric="results/simulation_time")

behavioursDict = TypedDict(
    "behavioursType", {"baseline": behaviour_controller.BaseBehaviourController}
)

behaviours: behavioursDict = {
    "baseline": custom_behaviour.BaselineBehaviourController(config_parser.config)
}

resultsDict = TypedDict(
    "resultsType",
    {
        "production": results_controller.CounterResultsController,
        "busyness": results_controller.TimesResultsController,
    },
)

wandb_data_dict = {}


def wandb_production_update_callback(
    controller: results_controller.CounterResultsController, index, time
):
    wandb_data_dict[f"results/production/{index.name}"] = controller.counters[index]


def wandb_time_update_callback(controller: results_controller.TimesResultsController):
    wandb_data_dict["results/times"] = {
        key: controller.times[key] for key in ["DIR04", "PT05", "PT06"]
    }
    wandb_data_dict["results/total_trays"] = custom_behaviour.tray_index


def wandb_busyness_update_callback(controller, busyness):
    wandb_data_dict["results/busyness"] = busyness


results: resultsDict = {
    "production": results_controller.CounterResultsController(
        custom_behaviour.ProductType, wandb_production_update_callback
    ),
    "busyness": results_controller.TimesResultsController(
        config_parser.config, wandb_time_update_callback, wandb_busyness_update_callback
    ),
}

step_to_time = 0.25
steps = 1000


def wandb_step_callback(core: desym.core.Simulation):
    if wandb_data_dict != {}:
        wandb_data_dict["results/simulation_time"] = (
            core.events_manager.step * step_to_time / 60
        )
        wandb.log(wandb_data_dict)
        wandb_data_dict.clear()

    check_simulation_errors(core)


def check_simulation_errors(core: desym.core.Simulation):
    # Loop over all stopper objects and check if any tray is located at two places at the same time

    tray_locations: Dict[str, list[str]] = {}
    for stopper in core.stoppers.values():
        if stopper.input_tray:
            if stopper.input_tray.tray_id in tray_locations:
                tray_locations[stopper.input_tray.tray_id].append(
                    stopper.stopper_id + " input"
                )
            else:
                tray_locations[stopper.input_tray.tray_id] = [
                    stopper.stopper_id + " input"
                ]
        output = 0
        for tray in stopper.output_trays.values():
            if tray:
                if tray.tray_id in tray_locations:
                    tray_locations[tray.tray_id].append(
                        stopper.stopper_id + f" output {output}"
                    )
                else:
                    tray_locations[tray.tray_id] = [
                        stopper.stopper_id + f" output {output}"
                    ]
            output += 1
    tray_string = ""
    for i in range(len(tray_locations)):
        tray_string += f"Tray {i} { [stopper_id for stopper_id in tray_locations[str(i)]] } --  "
    # logger.debug(f"S:{core.events_manager.step} - {tray_string}")

    for tray_id in tray_locations:
        if len(tray_locations[tray_id]) > 1:
            logger.error(f"Tray {tray_id} is located at {tray_locations[tray_id]}")
            raise Exception(f"Tray {tray_id} is located at {tray_locations[tray_id]}")

    # Check if all trays in simulation are located at some stopper
    for tray in core.trays:
        if tray.tray_id not in tray_locations:
            logger.error(f"Tray {tray} is not located at any stopper")
            raise Exception(f"Tray {tray} is not located at any stopper")


sim_core = desym.core.Simulation(
    config_parser.config, behaviours, results, wandb_step_callback
)

sim_core.config_steps(steps)
start = time.time()
sim_core.sim_runner()
logger.info(f"Simulation spent time: {time.time() - start}")
logger.info(f"Simulation duration: {steps*step_to_time / 3600} hours")
logger.debug(
    f'Production results {custom_behaviour.ProductType.product_0.name}: {results["production"].counters_timeseries[custom_behaviour.ProductType.product_0]}'
)
logger.info("Production results:")
logger.info(
    f'Product {custom_behaviour.ProductType.product_0.name}: {results["production"].counters[custom_behaviour.ProductType.product_0]}'
)
logger.info(
    f'Product {custom_behaviour.ProductType.product_1.name}: {results["production"].counters[custom_behaviour.ProductType.product_1]}'
)
logger.info(
    f'Product {custom_behaviour.ProductType.product_2.name}: {results["production"].counters[custom_behaviour.ProductType.product_2]}'
)
