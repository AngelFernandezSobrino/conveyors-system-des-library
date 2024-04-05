from __future__ import annotations
import argparse
import time
import os

from desim.events_manager import CustomEventListener
from sim import item

import logging

# import sim.checking as checking

from sim.item import Product

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


# def step_callback(core: desim.core.Simulation):
#     checking.time_one = time.time()
#     # wandb_wrapper.step_callback(core, wandb_enabled)

#     # checking.check_simulation_errors(core)
#     # checking.print_simulation_data(core)
#     # mqtt.send_data_to_mqtt(core)
#     checking.time_two = time.time()
#     # time.sleep(0.02)


## Create simulation core

sim_core = desim.core.Simulation[Product](config_parser.config, debug=args.verbose)

behavior = custom_behaviour.SimulationControllerReinforcedTraining(
    sim_core, settings.MAX_CONTAINERS_AMMOUNT
)

# sim_core.register_external_events(step_callback)

behavior.register_events()

for data_storage_step in range(0, settings.STEPS, 100):
    sim_core.timed_events_manager.add(
        CustomEventListener(
            data_storage.save_actual_results, (), {"controller": behavior}
        ),
        data_storage_step,
    )

## Create simulation graph analizer

# simulation_cycles_detector = graph.GraphAnalizer(sim_core)

## Run simulation

start = time.time()

sim_core.sim_run_steps(settings.STEPS)

print(sim_core.dump())

behavior.results_time.update_all_times()


## Print simulation results

logger.info(f"Simulation spent time: {time.time() - start}")
logger.info(
    f"Simulation duration: {sim_core.timed_events_manager.step*settings.STEP_TO_TIME / 60} min"
)
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

data_storage.save_data_to_file()
