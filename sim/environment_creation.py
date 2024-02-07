import os

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from typing import Dict

import desim.config_parser
from desim.objects.stopper.states import StateModel as StopperStateModel
from desim.objects.conveyor.states import StateModel as ConveyorStateModel
from sim import item

from sim.factory import get_simulator_config, create_simulator


class CustomEnv(gym.Env):
    """Custom Environment that follows gym interface."""

    metadata = {"render_modes": ["results_interface"]}

    def __init__(self, render_mode="results_interface"):
        super().__init__()

        self.simulator_config = get_simulator_config()
        self.simulator, self.simulator_controller = create_simulator(self.simulator_config)

        self.render_mode = render_mode
        # Define action and observation space
        # They must be gym.spaces objects
        # Example when using discrete actions:
        self.action_space = spaces.Discrete(3)
        # Example for using image as input (channel-first; channel-last also works):
        self.observation_space = spaces.Dict(
            {"stoppers": spaces.MultiDiscrete([
                [len(StopperStateModel.Node)] for _ in range(len(self.simulator.stoppers))]),
                "conveyors": spaces.MultiDiscrete([len(ConveyorStateModel.S) for _ in range(len(self.simulator.conveyors))])
            })

        self.product_serial_number_database: Dict[item.ProductTypeReferences, int] = {
            item.ProductTypeReferences.product_1: 1,
            item.ProductTypeReferences.product_2: 1,
            item.ProductTypeReferences.product_3: 1,
        }

        self.action_to_product_type = {
            0: item.ProductTypeReferences.product_1,
            1: item.ProductTypeReferences.product_2,
            2: item.ProductTypeReferences.product_3,
        }

    def step(self, action):

        terminated = False

        self.simulator.stop_simulation_signal = False

        product_to_load = self.action_to_product_type[action]

        self.product_serial_number_database[product_to_load] += 1

        self.simulator.stoppers['PT06'].container.load(
            item.Product(
                str(self.product_serial_number_database[product_to_load]),
                product_to_load, {}
            )
        )

        self.simulator.sim_run_steps(100000)

        if self.simulator.stop_simulation_signal:
            terminated = True

        observation = self.observation_from_simulator()
        reward = self.reward_from_simulator()

        truncated = False

        info = {}

        return observation, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        self.simulator, self.simulator_controller = create_simulator(self.simulator_config)

        self.simulator.sim_run_steps(100000)

        observation = self.observation_from_simulator()

        return observation, {}

    def render(self):
        print(self.observation_from_simulator())

    def close(self):
        pass


    def observation_from_simulator(self):
        return {
            "conveyors": [conveyors.s.state.value for conveyors in self.simulator.conveyors.values()],
            "stoppers": [stopper.s.state.node.value for stopper in self.simulator.stoppers.values()]
        }

    def reward_from_simulator(self):
        return self.simulator_controller.results_production.counters[item.ProductTypeReferences.product_1] + self.simulator_controller.results_production.counters[item.ProductTypeReferences.product_2]


if __name__ == "__main__":
    env = CustomEnv()
    print(env.observation_space.sample())
    print(env.action_space.sample())
    print(env.observation_space)
