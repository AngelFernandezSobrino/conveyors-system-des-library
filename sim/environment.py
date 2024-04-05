from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import gymnasium as gym
from gymnasium import spaces

from typing import Dict

import numpy as np
from sympy import N

import desim.config_parser
from sim import item, settings

from sim.environment_wrappers import (
    observation_from_simulator,
    reward_from_simulator,
    action_to_product_type,
)

if TYPE_CHECKING:
    import desim.core

from sim.factory import get_simulator_config, create_simulator_for_training


class CustomEnv(gym.Env):
    """Custom Environment that follows gym interface."""

    metadata = {"render_modes": ["results_interface"]}

    def __init__(
        self,
        max_containers: int = 10,
        simulation_time: float = 3600,
        step_to_time: float = 0.1,
        render_mode="ansi",
    ):
        super().__init__()

        self.simulator_config = get_simulator_config()

        self.max_containers = max_containers
        self.simulation_time = simulation_time
        self.step_to_time = step_to_time

        self.render_mode = render_mode

        # Create simulator for state observation definition
        self.simulator, self.simulator_controller = create_simulator_for_training(
            self.simulator_config,
            self.max_containers,
            self.simulation_time,
            self.step_to_time,
            debug=False,
        )

        # Define action and observation space
        # They must be gym.spaces objects
        # Example when using discrete actions:
        self.action_space = spaces.Discrete(3)
        # Example for using image as input (channel-first; channel-last also works):

        stopper_spaces_array = []

        for _ in range(len(self.simulator_config.config)):
            stopper_spaces_array.append(2)
            stopper_spaces_array.append(len(item.ProductTypeReferences) + 1)

        conveyor_spaces_array = []

        for _ in range(len(self.simulator.conveyors)):
            conveyor_spaces_array.append(2)
            conveyor_spaces_array.append(len(item.ProductTypeReferences) + 1)

        spaces_array = np.array([*stopper_spaces_array, *conveyor_spaces_array])

        self.observation_space = spaces.MultiDiscrete(spaces_array)

        self.product_serial_number_database: Dict[item.ProductTypeReferences, int] = {
            item.ProductTypeReferences.product_1: 1,
            item.ProductTypeReferences.product_2: 1,
            item.ProductTypeReferences.product_3: 1,
        }

    def step(self, action):
        terminated = False
        self.simulator.stop_simulation_signal = False

        product_to_load = action_to_product_type(action)

        self.product_serial_number_database[product_to_load] += 1

        if self.simulator.stoppers["PT06"].container is None:
            raise Exception("Container not found in PT06 stopper.")

        self.simulator.stoppers["PT06"].container.load(
            item.Product(
                str(self.product_serial_number_database[product_to_load]),
                product_to_load,
                {},
            )
        )

        self.simulator.sim_run_steps(settings.STEPS)

        if not self.simulator.stop_simulation_signal:
            truncated = False
        else:
            truncated = True

        observation = observation_from_simulator(self.simulator)
        reward = reward_from_simulator(self.simulator_controller)

        terminated = False
        info: dict = {}

        # print("Action: ", action)
        # print("Product: ", self.action_to_product_type[action])
        # print("Reward: ", reward)
        # print("Observation: ", observation)
        # print("Terminated: ", terminated)
        # print("Truncated: ", False)

        return observation, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        self.simulator, self.simulator_controller = create_simulator_for_training(
            self.simulator_config,
            self.max_containers,
            self.simulation_time,
            self.step_to_time,
            debug=False,
        )

        self.simulator.sim_run_steps(settings.STEPS)

        observation = observation_from_simulator(self.simulator)

        return observation, {}

    def render(self):
        return str(observation_from_simulator(self.simulator))

    def close(self):
        pass


if __name__ == "__main__":
    env = CustomEnv()
    print(env.observation_space.sample())
    print(env.action_space.sample())
    print(env.observation_space)
