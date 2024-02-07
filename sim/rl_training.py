from stable_baselines3 import PPO

from sim.environment_creation import CustomEnv

# Stable Baselines provides SimpleMultiObsEnv as an example environment with Dict observations
env = CustomEnv()

model = PPO("MultiInputPolicy", env, verbose=1)

model.learn(total_timesteps=10000)