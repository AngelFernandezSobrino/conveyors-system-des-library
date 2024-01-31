from __future__ import annotations
import argparse
import time
import os
from desim.events_manager import CustomEventListener
from sim import item

import logging

import sim.checking as checking

# import sim.mqtt as mqtt
import sim.settings as settings

# import sim.graph as graph
import sim.data_storage as data_storage

import desim.core
import desim.config_parser

import sim.controller as custom_behaviour


## Config desym module logging level

parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)

parser.add_argument("-v", "--verbose", action="store_true")  # on/off flag

args = parser.parse_args()

logger = logging.getLogger("mains")
logFormatter = logging.Formatter("\N{ESC}[0m{name: <30s} - {message}", style="{")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

if args.verbose:
    logging_level = logging.DEBUG
else:
    logging_level = logging.INFO

logger.setLevel(logging_level)

## Simulation configuration

config_path = os.path.dirname(os.path.abspath(__file__)) + "/config.xlsx"
config_parser = desim.config_parser.ConfigParser(config_path)
config_parser.parse("config_parser")

## Configure W&B

wandb_enabled = False

# import sim.wandb_wrapper as wandb_wrapper

# wandb_wrapper.config.data = config_parser.config

## Configure simulation behavior


## Step callback function for each simulation step


def step_callback(core: desim.core.Simulation):
    checking.time_one = time.time()
    # wandb_wrapper.step_callback(core, wandb_enabled)

    # checking.check_simulation_errors(core)
    # checking.print_simulation_data(core)
    # mqtt.send_data_to_mqtt(core)
    checking.time_two = time.time()
    # time.sleep(0.02)


## Create simulation core

sim_core = desim.core.Simulation(config_parser.config, debug=args.verbose)

behavior = custom_behaviour.SimulationController(sim_core)

sim_core.register_external_events(
    behavior.external_functions,
    step_callback,
)

for data_storage_step in range(0, settings.steps, 100):
    sim_core.timed_events_manager.add(
        CustomEventListener(
            data_storage.data_storage_update, (), {"controller": behavior}
        ),
        data_storage_step,
    )

## Create simulation graph analizer

# simulation_cycles_detector = graph.GraphAnalizer(sim_core)

## Run simulation

start = time.time()

sim_core.sim_run_steps(settings.steps)

behavior.results_time.update_all_times()


## Print simulation results

logger.info(f"Simulation spent time: {time.time() - start}")
logger.info(f"Simulation duration: {settings.steps*settings.step_to_time / 3600} hours")
logger.info("Production results:")
logger.info(
    f"Product {item.ProductTypeReferences.product_1.name}: {behavior.results_production.counters[item.ProductTypeReferences.product_1]}"
)
logger.info(
    f"Product {item.ProductTypeReferences.product_2.name}: {behavior.results_production.counters[item.ProductTypeReferences.product_2]}"
)
logger.info(
    f"Product {item.ProductTypeReferences.product_3.name}: {behavior.results_production.counters[item.ProductTypeReferences.product_3]}"
)

import csv

# Get the actual date and time string for the file name
from datetime import datetime

now = datetime.now()

# dd/mm/YY H:M:S
dt_string: str = now.strftime("%d-%m-%Y_%H-%M-%S")

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
            len(data_storage.data_dict["results/busyness"]) > busyness_step
            and data_storage.data_dict["results/busyness"][busyness_step][0] == step
        ):
            # logger.info(f"step: {step}, busyness: {data_storage.data_dict['results/busyness'][busyness_step][1]}")
            new_row.append(data_storage.data_dict["results/busyness"][busyness_step][1])
            busyness_step += 1
            write_row = True
        else:
            new_row.append(None)

        for index in ProductTypeReferences:
            if (
                len(data_storage.data_dict[f"results/production/{index.name}"])
                > production_step[f"results/production/{index.name}"]
                and data_storage.data_dict[f"results/production/{index.name}"][
                    production_step[f"results/production/{index.name}"]
                ][0]
                == step
            ):
                new_row.append(
                    data_storage.data_dict[f"results/production/{index.name}"][
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
