import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import time
import multiprocessing

from stable_baselines3 import DQN, PPO, A2C, DDPG
from sb3_contrib import QRDQN
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.vec_env import DummyVecEnv, VecVideoRecorder
from stable_baselines3.common.monitor import Monitor

from brickpong_gym_env import BrickPongEnv
import gymnasium as gym

# Directory to save models and results
MODEL_DIR = "rl_models"
VIDEO_DIR = "rl_videos"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# RL algorithms to compare (all discrete action)
algorithms = {
    "DQN": DQN,
    "QRDQN": QRDQN,
    "PPO": PPO,
    "A2C": A2C,
    "DDPG": DDPG,  # DDPG is for continuous, but included for completeness (will skip if not supported)
}

results = {}
NUM_TRAIN_STEPS = 30_000  # Lower for demo, increase for real training
NUM_EVAL_EPISODES = 15
VIDEO_LENGTH = 500  # Steps to record for video

N_CPUS = multiprocessing.cpu_count()

def make_env():
    return Monitor(BrickPongEnv(rl_mode=True))

def record_video(algo_name, model, env, video_length=VIDEO_LENGTH):
    # Wrap env for video recording
    venv = DummyVecEnv([lambda: Monitor(BrickPongEnv())])
    venv = VecVideoRecorder(
        venv, VIDEO_DIR, record_video_trigger=lambda x: x == 0,
        video_length=video_length, name_prefix=f"{algo_name}_agent"
    )
    obs = venv.reset()
    for _ in range(video_length):
        action, _ = model.predict(obs, deterministic=True)
        obs, _, dones, _ = venv.step(action)
        if dones[0]:
            obs = venv.reset()
    venv.close()

# Training and evaluation loop with tqdm and live plot
plt.ion()
fig, axs = plt.subplots(2, 1, figsize=(10, 10))
reward_lines = {}
winrate_bars = None

for algo_name, algo_class in algorithms.items():
    print(f"\n=== Training {algo_name} (visual mode) ===")
    # Use a single env for visualization
    env = Monitor(BrickPongEnv(rl_mode=False))
    model = algo_class("MlpPolicy", env, verbose=0)
    rewards = []
    for i in tqdm(range(NUM_TRAIN_STEPS), desc=f"Training {algo_name}", ncols=80):
        obs, _ = env.reset()
        done = False
        total_reward = 0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            total_reward += reward
            env.render()  # Show the game window
        rewards.append(total_reward)
    model.save(os.path.join(MODEL_DIR, f"{algo_name}_model"))
    env.close()

for algo_name, algo_class in algorithms.items():
    print(f"\n=== Training {algo_name} ===")
    # Use vectorized environments for parallelism
    env = DummyVecEnv([make_env for _ in range(N_CPUS)])
    model = algo_class("MlpPolicy", env, verbose=0)
    rewards = []
    pbar = tqdm(total=NUM_TRAIN_STEPS, desc=f"Training {algo_name}", ncols=80)
    callback_steps = NUM_TRAIN_STEPS // 20  # For live plotting

    # Custom training loop for live progress
    for i in range(0, NUM_TRAIN_STEPS, callback_steps):
        model.learn(total_timesteps=callback_steps, reset_num_timesteps=False, progress_bar=False)
        # Evaluate briefly for live plot
        mean_reward, _ = evaluate_policy(model, env, n_eval_episodes=3, return_episode_rewards=False)
        rewards.append(mean_reward)
        pbar.update(callback_steps)
        # Live plot
        axs[0].cla()
        for name, r in results.items():
            axs[0].plot(r["live_rewards"], label=name)
        axs[0].plot(rewards, label=algo_name, linewidth=3)
        axs[0].set_title("Live Mean Reward During Training")
        axs[0].set_xlabel("Eval Step")
        axs[0].set_ylabel("Mean Reward")
        axs[0].legend()
        plt.pause(0.01)
    pbar.close()

    # Save model
    model.save(os.path.join(MODEL_DIR, f"{algo_name}_model"))

    # Evaluate and record video
    print(f"Evaluating {algo_name}...")
    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=NUM_EVAL_EPISODES, return_episode_rewards=False)
    episode_rewards = []
    win_count = 0
    for _ in tqdm(range(NUM_EVAL_EPISODES), desc=f"Evaluating {algo_name}", ncols=80):
        obs = env.reset()
        done = False
        total_reward = 0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            total_reward += reward
        episode_rewards.append(total_reward)
        if "winner" in info and info["winner"] == "agent":
            win_count += 1

    # Record a video of the trained agent
    print(f"Recording video for {algo_name}...")
    record_video(algo_name, model, env)

    results[algo_name] = {
        "rewards": episode_rewards,
        "mean_reward": np.mean(episode_rewards),
        "win_rate": win_count / NUM_EVAL_EPISODES,
        "live_rewards": rewards
    }
    print(f"{algo_name}: Mean Reward = {results[algo_name]['mean_reward']:.2f}, Win Rate = {results[algo_name]['win_rate']:.2f}")

# Final plots
plt.ioff()
fig, axs = plt.subplots(2, 1, figsize=(10, 10))

# Rewards per episode
for algo_name in results:
    axs[0].plot(results[algo_name]["rewards"], label=f"{algo_name} (win rate: {results[algo_name]['win_rate']:.2f})")
axs[0].set_xlabel("Evaluation Episode")
axs[0].set_ylabel("Total Reward")
axs[0].set_title("RL Algorithm Comparison: Rewards per Episode")
axs[0].legend()
axs[0].grid(True)

# Bar plot for win rates
win_rates = [results[algo]["win_rate"] for algo in results]
axs[1].bar(list(results.keys()), win_rates, color='skyblue')
axs[1].set_ylabel("Win Rate")
axs[1].set_title("RL Algorithm Comparison: Win Rates")
axs[1].set_ylim(0, 1)
axs[1].grid(axis='y')

plt.tight_layout()
plt.savefig("rl_algorithms_comparison.png")
plt.show()

print("\nTraining, evaluation, and video recording complete. Models and plots saved.")
print(f"Check the '{VIDEO_DIR}' folder for agent gameplay videos!")