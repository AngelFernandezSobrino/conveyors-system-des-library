from __future__ import annotations
from typing import TYPE_CHECKING
import os

from stable_baselines3 import PPO

from desim.events_manager import CustomEventListener

from sim.item import Product
import sim.settings as settings

import sim.data_storage as data_storage

import desim.core

if TYPE_CHECKING:
    import desim.config_parser

import sim.controller as custom_behaviour


def get_simulator_config():

    config_path = os.path.dirname(os.path.abspath(__file__)) + "/config.xlsx"
    config_parser = desim.config_parser.ConfigParser(config_path)
    config_parser.parse("config_parser")

    return config_parser


def create_simulator_for_training(
    config_parser,
    max_containers: int,
    simulation_time: float,
    step_to_time: float,
    debug: bool = False,
) -> tuple[
    desim.core.Simulation[Product], custom_behaviour.SimulationControllerBaseline
]:

    sim_core = desim.core.Simulation[Product](config_parser.config, debug=debug)

    behavior = custom_behaviour.SimulationControllerReinforcedTraining(
        sim_core, max_containers_ammount=max_containers
    )

    behavior.register_events()

    for data_storage_step in range(0, settings.STEPS, 100):
        sim_core.timed_events_manager.add(
            CustomEventListener(
                data_storage.save_actual_results, (), {"controller": behavior}
            ),
            data_storage_step,
        )

    return sim_core, behavior


def create_simulator_for_testing(
    config_parser,
    max_containers: int,
    simulation_time: float,
    step_to_time: float,
    rl_model: PPO,
    debug: bool = False,
) -> tuple[
    desim.core.Simulation[Product], custom_behaviour.SimulationControllerBaseline
]:

    sim_core = desim.core.Simulation[Product](config_parser.config, debug=debug)

    behavior = custom_behaviour.SimulationControllerReinforcedAlgorithm(
        sim_core, max_containers, rl_model
    )

    behavior.register_events()

    for data_storage_step in range(0, settings.STEPS, 100):
        sim_core.timed_events_manager.add(
            CustomEventListener(
                data_storage.save_actual_results, (), {"controller": behavior}
            ),
            data_storage_step,
        )

    return sim_core, behavior
