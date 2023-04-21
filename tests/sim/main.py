from statistics import mean
import sys
import time
import os
from typing import Dict, List, Tuple, TypedDict, TYPE_CHECKING

import logger
import logging

import checking
import mqtt
import settings
import graph

if TYPE_CHECKING:
    import desym.objects.tray

import desym.helpers
import desym.core
import desym.objects.stopper.core
import desym.controllers.results_controller as results_controller
import desym.controllers.behavior_controller as behavior_controller

import behavior as custom_behaviour

## Config desym module logging level

logging.getLogger("desym").setLevel(logging.INFO)

## Simulation configuration

config_path = os.path.dirname(os.path.abspath(__file__)) + "/config.xlsx"
config_parser = desym.helpers.ConfigParser(config_path)
config_parser.parse("config_parser")

## Configure W&B

wandb_enabled = False
import wandb

wandb.config.data = config_parser.config

## Configure simulation behavior

behaviors = {
    "baseline": custom_behaviour.BaselineBehaviourController(config_parser.config)
}

results = {
    "production": results_controller.CounterResultsController(
        custom_behaviour.ProductType._member_names_, wandb.production_update_callback
    ),
    "busyness": results_controller.TimesResultsController(
        config_parser.config, wandb.time_update_callback, wandb.busyness_update_callback
    ),
}

## Step callback function for each simulation step


def step_callback(core: desym.core.Simulation):
    checking.time_one = time.time()
    wandb.step_callback(core, wandb_enabled)
    checking.check_simulation_errors(core)
    checking.print_simulation_data(core)
    mqtt.send_data_to_mqtt(core)
    checking.time_two = time.time()
    time.sleep(0.02)


## Create simulation core

# type: ignore
sim_core = desym.core.Simulation[custom_behaviour.BaseBehaviourController, results_controller.CounterResultsController | results_controller.TimesResultsController](
    config_parser.config, behaviors, results, step_callback
)

## Create simulation graph analizer

simulation_cycles = graph.GraphAnalizer(sim_core)

## Run simulation

sim_core.config_steps(settings.steps)
start = time.time()
sim_core.sim_runner()

## Print simulation results

logger.info(f"Simulation spent time: {time.time() - start}")
logger.info(f"Simulation duration: {settings.steps*settings.step_to_time / 3600} hours")
logger.debug(
    f'Production results {custom_behaviour.ProductType.product_1.name}: {results["production"].counters_timeseries[custom_behaviour.ProductType.product_1]}'
)
logger.info("Production results:")
logger.info(
    f'Product {custom_behaviour.ProductType.product_1.name}: {results["production"].counters[custom_behaviour.ProductType.product_1]}'
)
logger.info(
    f'Product {custom_behaviour.ProductType.product_2.name}: {results["production"].counters[custom_behaviour.ProductType.product_2]}'
)
logger.info(
    f'Product {custom_behaviour.ProductType.product_3.name}: {results["production"].counters[custom_behaviour.ProductType.product_3]}'
)
