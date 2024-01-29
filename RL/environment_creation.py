def get_products_location():
    NotImplemented


# %%
# Declaration and Initialization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Our custom environment will inherit from the abstract class
# ``gymnasium.Env``. You shouldn’t forget to add the ``metadata``
# attribute to your class. There, you should specify the render-modes that
# are supported by your environment (e.g. ``"human"``, ``"rgb_array"``,
# ``"ansi"``) and the framerate at which your environment should be
# rendered. Every environment should support ``None`` as render-mode; you
# don’t need to add it in the metadata. In ``GridWorldEnv``, we will
# support the modes “rgb_array” and “human” and render at 4 FPS.
#
# The ``__init__`` method of our environment will accept the integer
# ``size``, that determines the size of the square grid. We will set up
# some variables for rendering and define ``self.observation_space`` and
# ``self.action_space``. In our case, observations should provide
# information about the location of the agent and target on the
# 2-dimensional grid. We will choose to represent observations in the form
# of dictionaries with keys ``"agent"`` and ``"target"``. An observation
# may look like ``{"agent": array([1, 0]), "target": array([0, 3])}``.
# Since we have 4 actions in our environment (“right”, “up”, “left”,
# “down”), we will use ``Discrete(4)`` as an action space. Here is the
# declaration of ``GridWorldEnv`` and the implementation of ``__init__``:

import numpy as np

import gymnasium as gym
from gymnasium import spaces

import argparse
from statistics import mean
import time
import os
from typing import List, Union
from tests.sim.item import ProductTypeReferences

import sys

from tests.sim.logger import logger
import logging

import tests.sim.checking as checking
import tests.sim.mqtt as mqtt
import tests.sim.settings as settings
import tests.sim.graph as graph
import tests.sim.data_storage as data_storage

import desim.core
import desim.controllers.results_controller as results_controller
import tests.sim.behavior as custom_behaviour

## Config desym module logging level

parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)

parser.add_argument("-v", "--verbose", action="store_true")  # on/off flag

args = parser.parse_args()

print(args.verbose)

if args.verbose:
    logging_level = logging.DEBUG
else:
    logging_level = logging.INFO

logging.getLogger("desym").setLevel(logging_level)

## Simulation configuration

config_path = os.path.dirname(os.path.abspath(__file__)) + "/config.xlsx"
config_parser = desim.helpers.ConfigParser(config_path)
config_parser.parse("config_parser")

## Configure W&B

wandb_enabled = False

## Configure simulation behavior

behavior_baseline = custom_behaviour.BaselineBehaviourController(config_parser.config)


def production_update_callback(*args, **kwargs) -> None:
    data_storage.production_update_callback(*args, **kwargs)


def time_update_callback(*args, **kwargs):
    data_storage.time_update_callback(*args, **kwargs)


def busyness_update_callback(*args, **kwargs):
    data_storage.busyness_update_callback(*args, **kwargs)


results_production = results_controller.CounterResultsController(
    custom_behaviour.ProductTypeReferences, production_update_callback
)
results_time = results_controller.TimesResultsController(
    config_parser.config,
    time_update_callback,
    busyness_update_callback,
)

## Step callback function for each simulation step


def step_callback(core: desim.core.Simulation):
    checking.time_one = time.time()
    checking.time_two = time.time()


## Create simulation core

sim_core = desim.core.Simulation[
    custom_behaviour.BaseBehaviourController,
    results_controller.CounterResultsController
    | results_controller.TimesResultsController,
](
    config_parser.config,
    {"baseline": behavior_baseline},
    {"production": results_production, "busyness": results_time},
    step_callback,
)

## Create simulation graph analizer

simulation_cycles_detector = graph.GraphAnalizer(sim_core)

## Run simulation

start = time.time()

results_production.simulation_start(
    sim_core.stoppers, sim_core.timed_events_manager.step
)
results_time.simulation_start(sim_core.stoppers, sim_core.timed_events_manager.step)

sim_core.sim_run_steps(settings.steps)

results_production.simulation_end(sim_core.stoppers, sim_core.timed_events_manager.step)
results_time.simulation_end(sim_core.stoppers, sim_core.timed_events_manager.step)


class SimEnv(gym.Env):
    metadata = {"render_modes": ["None"]}

    def __init__(self, render_mode=None, size=5):
        self.size = size  # The size of the square grid
        self.window_size = 512  # The size of the PyGame window

        # Observations are dictionaries with the agent's and the target's location.
        # Each location is encoded as an element of {0, ..., `size`}^2, i.e. MultiDiscrete([size, size]).
        self.observation_space = spaces.Dict(
            {
                "products": spaces.Graph(
                    node_space=spaces.Discrete(3), edge_space=spaces.Discrete(3)
                ),
                "states": spaces.Graph(
                    node_space=spaces.Discrete(20), edge_space=spaces.Discrete(20)
                ),
            }
        )
        self.observation_space = spaces.Graph(
            node_space=spaces.Discrete(20), edge_space=spaces.Discrete(20)
        )
        # We have 4 actions, corresponding to "right", "up", "left", "down"
        self.action_space = spaces.Discrete(1)

        """
        The following dictionary maps abstract actions from `self.action_space` to
        the direction we will walk in if that action is taken.
        I.e. 0 corresponds to "right", 1 to "up" etc.
        """
        self._action_to_direction = {
            0: np.array(0),
            1: np.array(1),
        }

        self.render_mode = None

        """
        If human-rendering is used, `self.window` will be a reference
        to the window that we draw to. `self.clock` will be a clock that is used
        to ensure that the environment is rendered at the correct framerate in
        human-mode. They will remain `None` until human-mode is used for the
        first time.
        """
        self.window = None
        self.clock = None

    # %%
    # Constructing Observations From Environment States
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #
    # Since we will need to compute observations both in ``reset`` and
    # ``step``, it is often convenient to have a (private) method ``_get_obs``
    # that translates the environment’s state into an observation. However,
    # this is not mandatory and you may as well compute observations in
    # ``reset`` and ``step`` separately:

    def _get_obs(self):
        return {"products": self._products_location, "states": self._nodes_states}

    # %%
    # We can also implement a similar method for the auxiliary information
    # that is returned by ``step`` and ``reset``. In our case, we would like
    # to provide the manhattan distance between the agent and the target:

    def _get_info(self):
        return {
            "accumulated_production": self._accumulated_production,
        }

    # %%
    # Oftentimes, info will also contain some data that is only available
    # inside the ``step`` method (e.g. individual reward terms). In that case,
    # we would have to update the dictionary that is returned by ``_get_info``
    # in ``step``.

    # %%
    # Reset
    # ~~~~~
    #
    # The ``reset`` method will be called to initiate a new episode. You may
    # assume that the ``step`` method will not be called before ``reset`` has
    # been called. Moreover, ``reset`` should be called whenever a done signal
    # has been issued. Users may pass the ``seed`` keyword to ``reset`` to
    # initialize any random number generator that is used by the environment
    # to a deterministic state. It is recommended to use the random number
    # generator ``self.np_random`` that is provided by the environment’s base
    # class, ``gymnasium.Env``. If you only use this RNG, you do not need to
    # worry much about seeding, *but you need to remember to call
    # ``super().reset(seed=seed)``* to make sure that ``gymnasium.Env``
    # correctly seeds the RNG. Once this is done, we can randomly set the
    # state of our environment. In our case, we randomly choose the agent’s
    # location and the random sample target positions, until it does not
    # coincide with the agent’s position.
    #
    # The ``reset`` method should return a tuple of the initial observation
    # and some auxiliary information. We can use the methods ``_get_obs`` and
    # ``_get_info`` that we implemented earlier for that:

    def reset(self, seed=None, options=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        # Choose the agent's location uniformly at random
        self._products_location = get_products_location()

        # We will sample the target's location randomly until it does not coincide with the agent's location
        self._nodes_states = self._products_location
        while np.array_equal(self._nodes_states, self._products_location):
            self._nodes_states = self.np_random.integers(
                0, self.size, size=2, dtype=int
            )

        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()

        return observation, info

    # %%
    # Step
    # ~~~~
    #
    # The ``step`` method usually contains most of the logic of your
    # environment. It accepts an ``action``, computes the state of the
    # environment after applying that action and returns the 5-tuple
    # ``(observation, reward, terminated, truncated, info)``. See
    # :meth:`gymnasium.Env.step`. Once the new state of the environment has
    # been computed, we can check whether it is a terminal state and we set
    # ``done`` accordingly. Since we are using sparse binary rewards in
    # ``GridWorldEnv``, computing ``reward`` is trivial once we know
    # ``done``.To gather ``observation`` and ``info``, we can again make
    # use of ``_get_obs`` and ``_get_info``:

    def step(self, action):
        # Map the action (element of {0,1,2,3}) to the direction we walk in
        direction = self._action_to_direction[action]
        # We use `np.clip` to make sure we don't leave the grid
        self._products_location = np.clip(
            self._products_location + direction, 0, self.size - 1
        )
        # An episode is done iff the agent has reached the target
        terminated = np.array_equal(self._products_location, self._nodes_states)
        reward = 1 if terminated else 0  # Binary sparse rewards
        observation = self._get_obs()
        info = self._get_info()

        return observation, reward, terminated, False, info

    # %%
    # Rendering
    # ~~~~~~~~~
    #
    # Here, we are using PyGame for rendering. A similar approach to rendering
    # is used in many environments that are included with Gymnasium and you
    # can use it as a skeleton for your own environments:

    def render(self):
        print("render")

    # %%
    # Close
    # ~~~~~
    #
    # The ``close`` method should close any open resources that were used by
    # the environment. In many cases, you don’t actually have to bother to
    # implement this method. However, in our example ``render_mode`` may be
    # ``"human"`` and we might need to close the window that has been opened:

    def close(self):
        return
