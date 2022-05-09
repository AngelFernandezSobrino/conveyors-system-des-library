from src import simulator
import controller_example
import controller_empty

if __name__ == '__main__':

    config_path = '../../data/simulator_config.xlsx'
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
    sim_core.run_steps(100)
    sim_core.start()
    sim_core.thread.join()
    print(sim_core.results_controller.times['0'])
    print(sim_core.results_controller.times['1'])
    print(sim_core.results_controller.times['2'])
    print(sim_core.results_controller.times['3'])
    print(sim_core.results_controller.times['4'])
