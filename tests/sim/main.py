
from statistics import mean
import sys
import time
import os
from typing import Dict, List, TypedDict

import logging

from desym.objects.item import Item

logger = logging.getLogger("main")
logFormatter = logging.Formatter(fmt="%(name)s: %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)

import paho.mqtt.publish
import paho.mqtt.client

import desym.helpers
import desym.core
import desym.objects.stopper.core
import desym.controllers.results_controller as results_controller
import desym.controllers.behaviour_controller as behaviour_controller
import behaviour as custom_behaviour

logging.getLogger("desym").setLevel(logging.INFO)

config_path = os.path.dirname(os.path.abspath(__file__)) + "/config.xlsx"
config_parser = desym.helpers.ConfigParser(config_path)
config_parser.parse("config_parser")

if not config_parser.config_available:
    raise Exception("Config not available")

wandb_enabled = False

if wandb_enabled:
    import wandb

    wandb.init(project="i4techlab-simulation", entity="soobbz")
    config = wandb.config
    config.data = config_parser.config
    wandb.define_metric("results/simulation_time")
    wandb.define_metric("results/*", step_metric="results/simulation_time")

behaviorsDict = TypedDict(
    "behaviorsDict", {"baseline": behaviour_controller.BaseBehaviourController}
)

behaviours: behaviorsDict = {
    "baseline": custom_behaviour.BaselineBehaviourController(config_parser.config)
}

resultsDict = TypedDict(
    "resultsDict",
    {
        "production": results_controller.CounterResultsController,
        "busyness": results_controller.TimesResultsController,
    },
)

wandb_data_dict: dict = {}


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
steps = 100000

time_one = time.time()
time_two = time.time()

sim_time_max: float = 0
sim_time_min: float = 20

callback_time_max: float = 0
callback_time_min: float = 20

sim_time_list: list[float] = []
callback_time_list: list[float] = []

calc_mean_interval = 0


def wandb_step_callback(core: desym.core.Simulation):
    if wandb_data_dict != {}:
        wandb_data_dict["results/simulation_time"] = (
            core.events_manager.step * step_to_time / 60
        )
        if wandb_enabled:
            wandb.log(wandb_data_dict)
        wandb_data_dict.clear()


lines_to_delete = 0


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

    # for i in range(len(tray_locations)):
    #     tray_string += (
    #         f"Tray {i} { [stopper_id for stopper_id in tray_locations[str(i)]] } \n "
    #     )
    #     next_lines_to_delete += 1

    for tray_id in tray_locations:
        if len(tray_locations[tray_id]) > 1:
            logger.error(f"Tray {tray_id} is located at {tray_locations[tray_id]}")
            raise Exception(f"Tray {tray_id} is located at {tray_locations[tray_id]}")

    # Check if all trays in simulation are located at some stopper
    for tray in core.trays:
        if tray.tray_id not in tray_locations:
            logger.error(f"Tray {tray} is not located at any stopper")
            raise Exception(f"Tray {tray} is not located at any stopper")

    # Check if all trays have different items
    tray_items: Dict[str, list[Item]] = {}
    for tray in core.trays:
        if not tray.item:
            break
        if tray.tray_id in tray_items:
            tray_items[tray.tray_id].append(tray.item)
        else:
            tray_items[tray.tray_id] = [tray.item]

    for tray_id in tray_items:
        if len(tray_items[tray_id]) > 1:
            logger.error(f"Tray {tray_id} has items {tray_items[tray_id]}")
            raise Exception(f"Tray {tray_id} has items {tray_items[tray_id]}")


def print_simulation_data(core: desym.core.Simulation):
    global lines_to_delete
    next_lines_to_delete = 2
    tray_string = ""
    for stopper in core.stoppers.values():
        tray_string += f"Stopper {stopper.stopper_id} input: {stopper.input_tray.tray_id if stopper.input_tray is not None else None } { [tray.tray_id if tray is not None else None for tray in stopper.output_trays.values()]} \n "
        next_lines_to_delete += 1
    global sim_time_max, sim_time_min, callback_time_max, callback_time_min, calc_mean_interval
    sim_time = (time_one - time_two) * 1000
    callback_time = (time.time() - time_one) * 1000
    if sim_time > sim_time_max:
        sim_time_max = sim_time
    if sim_time < sim_time_min:
        sim_time_min = sim_time
    if callback_time > callback_time_max:
        callback_time_max = callback_time
    if callback_time < callback_time_min:
        callback_time_min = callback_time

    if calc_mean_interval == 10:
        sim_time_list.append(sim_time)
        callback_time_list.append(callback_time)
        calc_mean_interval = 0

    calc_mean_interval += 1

    sim_time_mean = 0
    callback_time_mean = 0

    # Calculate mean values
    if len(sim_time_list) > 100:
        sim_time_list.pop(0)
        callback_time_list.pop(0)
    if len(sim_time_list) > 0:
        sim_time_mean = sum(sim_time_list) / len(sim_time_list)
        callback_time_mean = sum(callback_time_list) / len(callback_time_list)
    for i in range(lines_to_delete):
        LINE_UP = "\033[1A"
        LINE_CLEAR = "\x1b[2K"
        print(LINE_UP, end=LINE_CLEAR)
    lines_to_delete = next_lines_to_delete
    print(
        f"Step:{core.events_manager.step} Sim time:"
        + "{:4.4f}".format(sim_time)
        + " Max: "
        + "{:4.4f}".format(sim_time_max)
        + " Min: "
        + "{:4.4f}".format(sim_time_min)
        + " Mean: "
        + "{:4.4f}".format(sim_time_mean)
        + " Callback time:"
        + "{:4.4f}".format(callback_time)
        + " Max: "
        + "{:4.4f}".format(callback_time_max)
        + " Min: "
        + "{:4.4f}".format(callback_time_min)
        + " Mean: "
        + "{:4.4f}".format(callback_time_mean)
        + f" \n {tray_string}"
    )


def send_data_to_mqtt(core: desym.core.Simulation):
    msg_list = [("desym/step", str(core.events_manager.step), 0, False)]

    for stopper in core.stoppers.values():
        if stopper.input_tray is not None:
            if stopper.input_tray.item:
                item_string = f" T: {stopper.input_tray.item.item_type.value} S: {stopper.input_tray.item.state}"
            else:
                item_string = ""
            msg_list.append(
                (
                    f"desym/stopper/{stopper.stopper_id}/input",
                    str(f"Id: {stopper.input_tray.tray_id} {item_string}"),
                    0,
                    False,
                )
            )
        else:
            msg_list.append(
                (f"desym/stopper/{stopper.stopper_id}/input", None, 0, False)
            )

        for output_tray_id in stopper.output_trays:
            if stopper.output_trays[output_tray_id]:
                if stopper.output_trays[output_tray_id].item:
                    item_string = f"T: {stopper.output_trays[output_tray_id].item.item_type.value} S: {stopper.output_trays[output_tray_id].item.state}"
                else:
                    item_string = ""
                msg_list.append(
                    (
                        f"desym/stopper/{stopper.stopper_id}/output/{output_tray_id}",
                        str(
                            f"Id: {stopper.output_trays[output_tray_id].tray_id} {item_string}"
                        ),
                        0,
                        False,
                    )
                )
            else:
                msg_list.append(
                    (
                        f"desym/stopper/{stopper.stopper_id}/output/{output_tray_id}",
                        None,
                        0,
                        False,
                    )
                )

    paho.mqtt.publish.multiple(
        msg_list,
        hostname="localhost",
        port=1883,
        client_id="",
        keepalive=60,
        will=None,
        auth=None,
        tls=None,
        protocol=paho.mqtt.client.MQTTv311,
        transport="tcp",
    )


def step_callback(core: desym.core.Simulation):
    global time_one, time_two
    time_one = time.time()
    wandb_step_callback(core)
    check_simulation_errors(core)
    print_simulation_data(core)
    send_data_to_mqtt(core)
    time_two = time.time()
    time.sleep(0.02)


# Function to activate stopper locks to avoid deadlocks
# It checks the population of the different cycles present in the graph representation of the simulation
# If the population of a cycle is equal to the number of stoppers in the cycle less one, it locks all the stoppers that enter the cycle
# If the population of a cycle is les than the number of stoppers in the cycle less one, it unlocks all the stoppers that enter the cycle
def calculate_cycles_saturation(core: desym.core.Simulation):
    pass

cycle = List[desym.objects.stopper.core.Stopper]

class GraphAnalizer:
    def __init__(
        self,
        stoppers: dict[
            desym.objects.stopper.core.StopperId, desym.objects.stopper.core.Stopper
        ],
    ):
        # Dictionary with the output stoppers of each stopper that colide with a foreign cycle
        self.inputs_cycles_to_check: dict[
            desym.objects.stopper.core.StopperId,
            dict[
                desym.objects.stopper.core.StopperId,
                list[cycle],
            ],
        ] = {}

        self.stoppers = stoppers
        self.visited: dict[desym.objects.stopper.core.StopperId, bool] = {}
        self.stack: list[desym.objects.stopper.core.StopperId] = []
        self.cycles: list[cycle] = []
        self.path: list[desym.objects.stopper.core.Stopper] = []

        self.find_cycles()
        self.calculate_consideration_list()

    def find_cycles(self):
        for stopper in self.stoppers.values():
            self.visited[stopper.stopper_id] = False

        self.dfs(self.stoppers["PT01"])

        return GraphAnalizer

    def dfs(self, stopper: desym.objects.stopper.core.Stopper):
        self.visited[stopper.stopper_id] = True
        self.path.append(stopper)

        for output_stopper in stopper.output_stoppers:
            if output_stopper in self.path:
                cycle_start = self.path.index(output_stopper)
                self.cycles.append(self.path[cycle_start:])
            else:
                if not self.visited[output_stopper.stopper_id]:
                    self.dfs(output_stopper)
            # No else clause is needed since we don't need to do anything if we have already visited the node.

        self.path.pop()
        self.visited[stopper.stopper_id] = False

    # Calculate the consideration list. It has, for each stopper of the simulation, a dict for each input stopper with list of cycles where the stopper is present but the input stopper is not.
    def calculate_consideration_list(self):
        for stopper in self.stoppers.values():
            for input_stopper in stopper.input_stoppers:
                for cycle in self.cycles:
                    if input_stopper not in cycle and stopper in cycle:
                        if stopper.stopper_id not in self.inputs_cycles_to_check:
                            self.inputs_cycles_to_check[stopper.stopper_id] = {}
                        if input_stopper.stopper_id not in self.inputs_cycles_to_check[stopper.stopper_id]:
                            self.inputs_cycles_to_check[stopper.stopper_id][input_stopper.stopper_id] = [cycle]
                        elif cycle not in self.inputs_cycles_to_check[stopper.stopper_id][input_stopper.stopper_id]:
                            self.inputs_cycles_to_check[stopper.stopper_id][input_stopper.stopper_id].append(cycle)


sim_core = desym.core.Simulation(
    config_parser.config, behaviours, results, wandb_step_callback
)

simulation_cycles = GraphAnalizer(sim_core.stoppers)


sim_core.config_steps(steps)
start = time.time()
sim_core.sim_runner()
logger.info(f"Simulation spent time: {time.time() - start}")
logger.info(f"Simulation duration: {steps*step_to_time / 3600} hours")
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
