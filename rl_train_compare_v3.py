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

def train_batch(algo_name, algo_class, batch_id, return_dict):
    env = Monitor(BrickPongEnv(rl_mode=True))
    model = algo_class("MlpPolicy", env, verbose=0)
    rewards = []
    for i in range(500):
        obs, _ = env.reset()
        done = False
        total_reward = 0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            total_reward += reward
        rewards.append(total_reward)
    avg_reward = np.mean(rewards)
    model_path = f"{MODEL_DIR}/{algo_name}_batch{batch_id}_model"
    model.save(model_path)
    return_dict[batch_id] = (avg_reward, model_path)
    env.close()

if __name__ == "__main__":
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    algo_name = "DQN"  # Or any from your algorithms
    algo_class = algorithms[algo_name]
    jobs = []
    for batch_id in range(N_CPUS):
        p = multiprocessing.Process(target=train_batch, args=(algo_name, algo_class, batch_id, return_dict))
        p.start()
        jobs.append(p)
    for p in jobs:
        p.join()

    # Find best model
    best_batch = max(return_dict.items(), key=lambda x: x[1][0])
    best_model_path = best_batch[1][1]
    print(f"Best model: {best_model_path} with avg reward {best_batch[1][0]}")

    # Visualize and continue training with best model
    env = Monitor(BrickPongEnv(rl_mode=False))
    model = algo_class.load(best_model_path, env=env)
    for i in tqdm(range(500, NUM_TRAIN_STEPS), desc="Visual Training"):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            env.render()
    env.close()

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