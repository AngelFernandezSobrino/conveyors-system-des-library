from stable_baselines3 import PPO

from sim.environment import CustomEnv
from sim.environment_wrappers import observation_from_simulator
from stable_baselines3.common.evaluation import evaluate_policy

env = CustomEnv()

env.reset()

print(env.observation_space)

print(observation_from_simulator(env.simulator))

model = PPO("MlpPolicy", env, tensorboard_log="../tensorboard_logs/")


model.learn(total_timesteps=2000, progress_bar=True, tb_log_name="PPO_v1")

mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=100)

print(f"mean_reward:{mean_reward:.2f} +/- {std_reward:.2f}")
