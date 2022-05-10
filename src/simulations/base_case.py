import simulator
import time
import controller_example
import controller_empty

if __name__ == '__main__':

    config_path = '../../data/simulator_config_v3.xlsx'
    config_parser = simulator.ConfigParser(config_path)
    config_parser.parse('config_parser')

    if not config_parser.config_available:
        raise Exception('Config not available')

    behaviour_controller = controller_example.ControllerExample(config_parser.config)

    behaviour_controller2 = controller_empty.ControllerExample(config_parser.config)

    results_controller = simulator.ResultsController(config_parser.config)

    sim_core = simulator.Core(config_parser.config, behaviour_controller2, results_controller)

    print('Running simulation...')
    print('Run steps')
    sim_core.run_steps(200000)
    start = time.time()
    sim_core.start()
    sim_core.thread.join()
    print(time.time() - start)
    # for i in config_parser.config.keys():
    #     print(sim_core.results_controller.times[i])
