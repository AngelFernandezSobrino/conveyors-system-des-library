import time
import os
from typing import Dict, TypedDict

import sim.helpers
import sim.core
import sim.controllers.results_controller as results_controller
import sim.controllers.behaviour_controller as behaviour_controller
import behaviour as custom_behaviour

config_path = os.path.dirname(os.path.abspath(__file__)) + "/config.xlsx"
config_parser = sim.helpers.ConfigParser(config_path)
config_parser.parse("config_parser")

# import wandb
# wandb.init(project="i4techlab-simulation-tests", entity="soobbz")


if not config_parser.config_available:
    raise Exception("Config not available")

# config = wandb.config
# config.data = config_parser.config

behavioursDict = TypedDict('behavioursType', {"baseline": behaviour_controller.BaseBehaviourController})

behaviours: behavioursDict = {
    "baseline": custom_behaviour.BaselineBehaviourController(
        config_parser.config
    )
}

resultsDict = TypedDict('resultsType', {"production": results_controller.CounterController, "busyness": results_controller.TimesController})

results: resultsDict = {
    "production": results_controller.CounterController(
        custom_behaviour.ProductType
    ),
    "busyness": results_controller.TimesController(config_parser.config),
}

sim_core = sim.core.Core(config_parser.config, behaviours, results)

print("Running simulation...")
print("Run steps")
sim_core.config_steps(1000000)
start = time.time()
sim_core.sim_runner()
print(time.time() - start)
print(results["production"].counter_history[custom_behaviour.ProductType.product_0])
print(f"production_{custom_behaviour.ProductType.product_0.name}")

# wandb.log(
#     {
#         "production": {
#             custom_behaviour.ProductType.product_0.name: wandb.Table(
#                 data=results["production"].counter_history[
#                     custom_behaviour.ProductType.product_0
#                 ],
#                 columns=["step", "production"],
#             ),
#             custom_behaviour.ProductType.product_1.name: wandb.Table(
#                 data=results["production"].counter_history[
#                     custom_behaviour.ProductType.product_1
#                 ],
#                 columns=["step", "production"],
#             ),
#             custom_behaviour.ProductType.product_2.name: wandb.Table(
#                 data=results["production"].counter_history[
#                     custom_behaviour.ProductType.product_2
#                 ],
#                 columns=["step", "production"],
#             ),
#         },
#         "busyness": wandb.Table(
#             data=results["busyness"].busyness, columns=["step", "busyness"]
#         ),
#     }
# )
