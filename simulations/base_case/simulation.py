import simulator

import time
import behaviour

import wandb

wandb.init(project="my-2-test-project", entity="soobbz")

config_path = '../../data/simulator_config_v3.xlsx'
config_parser = simulator.helpers.ConfigParser(config_path)
config_parser.parse('config_parser')

if not config_parser.config_available:
    raise Exception('Config not available')

wandb.config = config_parser.config

behaviour_controllers = [behaviour.BaselineBehaviourController(config_parser.config)]

results_controllers = [simulator.controllers.results_controller.ProductionResultsController(behaviour.ProductType),
                       simulator.controllers.results_controller.TimesResultsController(config_parser.config)]

sim_core = simulator.Core(config_parser.config, behaviour_controllers, results_controllers)

print('Running simulation...')
print('Run steps')
sim_core.config_steps(50000)
start = time.time()
sim_core.sim_runner()
print(time.time() - start)
print(results_controllers[0].production_history[behaviour.ProductType.product_0])
print(f'production_{behaviour.ProductType.product_0.name}')

wandb.log({
    "production": {
        behaviour.ProductType.product_0.name: wandb.Table(
            data=results_controllers[0].production_history[behaviour.ProductType.product_0],
            columns=['step', 'production', 'product_code']),
        behaviour.ProductType.product_1.name: wandb.Table(
            data=results_controllers[0].production_history[behaviour.ProductType.product_1],
            columns=['step', 'production', 'product_code']),
        behaviour.ProductType.product_2.name: wandb.Table(
            data=results_controllers[0].production_history[behaviour.ProductType.product_2],
            columns=['step', 'production', 'product_code']),
    },
    "busyness": wandb.Table(data=results_controllers[1].busyness, columns=["step", "busyness"])
})
