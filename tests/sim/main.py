import argparse
from statistics import mean
import time
import os
from typing import List, Union
from tests.sim.item import ProductTypeReferences

import sys

from tests.sim.logger import logger
import logging

import tests.sim.checking as checking
import tests.sim.mqtt as mqtt
import tests.sim.settings as settings
import tests.sim.graph as graph
import tests.sim.data_storage as data_storage

import desym.core
import desym.controllers.results_controller as results_controller
import tests.sim.behavior as custom_behaviour

## Config desym module logging level

parser = argparse.ArgumentParser(
                    prog='ProgramName',
                    description='What the program does',
                    epilog='Text at the bottom of help')

parser.add_argument('-v', '--verbose',
                    action='store_true')  # on/off flag

args = parser.parse_args()

print(args.verbose)

if args.verbose:
    logging_level = logging.DEBUG
else:
    logging_level = logging.INFO

logging.getLogger("desym").setLevel(logging_level)

## Simulation configuration

config_path = os.path.dirname(os.path.abspath(__file__)) + "/config.xlsx"
config_parser = desym.helpers.ConfigParser(config_path)
config_parser.parse("config_parser")

## Configure W&B

wandb_enabled = False

# import tests.sim.wandb_wrapper as wandb_wrapper

# wandb_wrapper.config.data = config_parser.config

## Configure simulation behavior

behavior_baseline = custom_behaviour.BaselineBehaviourController(config_parser.config)

def production_update_callback(
    *args, **kwargs
) -> None:
    data_storage.production_update_callback(*args, **kwargs)
    # wandb_wrapper.production_update_callback(*args, **kwargs)

def time_update_callback(
    *args, **kwargs
):
    data_storage.time_update_callback(*args, **kwargs)
    # wandb_wrapper.time_update_callback(*args, **kwargs)

def busyness_update_callback(*args, **kwargs):
    data_storage.busyness_update_callback(*args, **kwargs)
    # wandb_wrapper.busyness_update_callback(*args, **kwargs)


results_production = results_controller.CounterResultsController(
    custom_behaviour.ProductTypeReferences, production_update_callback
)
results_time = results_controller.TimesResultsController(
    config_parser.config,
    time_update_callback,
    busyness_update_callback,
)

## Step callback function for each simulation step


def step_callback(core: desym.core.Simulation):
    checking.time_one = time.time()
    # wandb_wrapper.step_callback(core, wandb_enabled)

    #checking.check_simulation_errors(core)
    #checking.print_simulation_data(core)
    #mqtt.send_data_to_mqtt(core)
    checking.time_two = time.time()
    # time.sleep(0.02)


## Create simulation core

sim_core = desym.core.Simulation[
    custom_behaviour.BaseBehaviourController,
    results_controller.CounterResultsController
    | results_controller.TimesResultsController,
](
    config_parser.config,
    {"baseline": behavior_baseline},
    {"production": results_production, "busyness": results_time},
    step_callback,
)

## Create simulation graph analizer

simulation_cycles_detector = graph.GraphAnalizer(sim_core)

## Run simulation

start = time.time()

results_production.simulation_start(sim_core.stoppers, sim_core.events_manager.step)
results_time.simulation_start(sim_core.stoppers, sim_core.events_manager.step)

sim_core.sim_run_steps(settings.steps)

results_production.simulation_end(sim_core.stoppers, sim_core.events_manager.step)
results_time.simulation_end(sim_core.stoppers, sim_core.events_manager.step)



## Print simulation results

logger.info(f"Simulation spent time: {time.time() - start}")
logger.info(f"Simulation duration: {settings.steps*settings.step_to_time / 3600} hours")
logger.debug(
    f"Production results {custom_behaviour.ProductTypeReferences.product_1.name}: {results_production.counters_timeseries[custom_behaviour.ProductTypeReferences.product_1]}"
)
logger.info("Production results:")
logger.info(
    f"Product {custom_behaviour.ProductTypeReferences.product_1.name}: {results_production.counters[custom_behaviour.ProductTypeReferences.product_1]}"
)
logger.info(
    f"Product {custom_behaviour.ProductTypeReferences.product_2.name}: {results_production.counters[custom_behaviour.ProductTypeReferences.product_2]}"
)
logger.info(
    f"Product {custom_behaviour.ProductTypeReferences.product_3.name}: {results_production.counters[custom_behaviour.ProductTypeReferences.product_3]}"
)

import csv


with open('data.csv', 'w') as f:

    busyness_step = 0
    production_step = {}
    for index in ProductTypeReferences:
        production_step[f"results/production/{index.name}"] = 0

    writer = csv.writer(f)
    writer.writerow(["step", "busyness", "production_1", "production_2", "production_3"])


    for step in range(-1, settings.steps):
        new_row: List[Union[float, None]] = [step]
        write_row = False
        if len(data_storage.data_dict["results/busyness"]) > busyness_step and data_storage.data_dict["results/busyness"][busyness_step][0] == step:
            # logger.info(f"step: {step}, busyness: {data_storage.data_dict['results/busyness'][busyness_step][1]}")
            new_row.append(data_storage.data_dict["results/busyness"][busyness_step][1])
            busyness_step += 1
            write_row = True
        else:
            new_row.append(None)

        for index in ProductTypeReferences:
            if len(data_storage.data_dict[f"results/production/{index.name}"]) > production_step[f"results/production/{index.name}"] and data_storage.data_dict[f"results/production/{index.name}"][production_step[f"results/production/{index.name}"]][0] == step:
                new_row.append(data_storage.data_dict[f"results/production/{index.name}"][production_step[f"results/production/{index.name}"]][1])
                # logger.info(f"step: {step}, production_1: "+ str(data_storage.data_dict[f"results/production/{index.name}"][production_step[f"results/production/{index.name}"]][1]))

                production_step[f"results/production/{index.name}"] += 1
                write_row = True
            else:
                new_row.append(None)
        if write_row:
            writer.writerow(new_row)


