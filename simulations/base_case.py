import simulator

simulation_api = simulator.Api('../data/simulator_config.xlsx')

print('Run simulation')

simulation_api.run_steps(10)
