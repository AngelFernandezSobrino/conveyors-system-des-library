import simulator
import time
import behaviour
import results
import wandb

wandb.init(project="my-test-project", entity="soobbz")


config_path = '../../data/simulator_config_v3.xlsx'
config_parser = simulator.ConfigParser(config_path)
config_parser.parse('config_parser')

if not config_parser.config_available:
    raise Exception('Config not available')

wandb.config = config_parser.config

behaviour_controller = behaviour.BehaviourController(config_parser.config)
results_controller = results.ResultsController(config_parser.config)

sim_core = simulator.Core(config_parser.config, behaviour_controller, results_controller)

print('Running simulation...')
print('Run steps')
sim_core.run_steps(50000)
start = time.time()
sim_core.start()
sim_core.thread.join()
print(time.time() - start)
for i in config_parser.config.keys():
    print(sim_core.results_controller.times[i])

wandb.log({"data": sim_core.results_controller.times})
