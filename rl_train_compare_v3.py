import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import time
import multiprocessing
import random

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

def train_batch(algo_name, algo_class, batch_id, return_dict, progress_queue, vis_queue):
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
        # Every 1000th episode, save model and notify for visualization
        if (i + 1) % 1000 == 0:
            model_path = f"{MODEL_DIR}/{algo_name}_batch{batch_id}_ep{i+1}_model"
            model.save(model_path)
            vis_queue.put((batch_id, i + 1, model_path))
        # Progress reporting
        if (i + 1) % 1000 == 0:
            progress_queue.put(1000)
    # Final model for batch
    model_path = f"{MODEL_DIR}/{algo_name}_batch{batch_id}_model"
    model.save(model_path)
    avg_reward = np.mean(rewards)
    return_dict[batch_id] = (avg_reward, model_path)
    # Report any remaining progress
    progress_queue.put((500 % 1000) or 500)
    env.close()

if __name__ == "__main__":
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    progress_queue = manager.Queue()
    vis_queue = manager.Queue()
    algo_name = "DQN"
    algo_class = algorithms[algo_name]
    jobs = []
    N_CPUS = multiprocessing.cpu_count()
    total_episodes = N_CPUS * 500
    for batch_id in range(N_CPUS):
        p = multiprocessing.Process(target=train_batch, args=(algo_name, algo_class, batch_id, return_dict, progress_queue, vis_queue))
        p.start()
        jobs.append(p)

    # Progress bar for batches (updates every 1000 episodes)
    with tqdm(total=total_episodes, desc="Parallel Batch Training") as pbar:
        finished = 0
        while finished < total_episodes:
            # Check for progress
            while not progress_queue.empty():
                update = progress_queue.get()
                pbar.update(update)
                finished += update
            # Check for visualization requests
            while not vis_queue.empty():
                batch_id, ep_num, model_path = vis_queue.get()
                print(f"\n[Visualizing] Batch {batch_id}, Episode {ep_num}")
                env = Monitor(BrickPongEnv(rl_mode=False))
                model = algo_class.load(model_path, env=env)
                obs, _ = env.reset()
                done = False
                while not done:
                    action, _ = model.predict(obs, deterministic=True)
                    obs, reward, terminated, truncated, info = env.step(action)
                    done = terminated or truncated
                    env.render()
                env.close()
            time.sleep(0.1)  # Prevent busy waiting
    for p in jobs:
        p.join()

    # Find best model
    best_batch = max(return_dict.items(), key=lambda x: x[1][0])
    best_model_path = best_batch[1][1]
    print(f"Best model: {best_model_path} with avg reward {best_batch[1][0]}")

    # Visualize a random batch model
    random_batch_id = random.choice(list(return_dict.keys()))
    random_model_path = return_dict[random_batch_id][1]
    print(f"Visualizing random batch: {random_batch_id} ({random_model_path})")
    env = Monitor(BrickPongEnv(rl_mode=False))
    model = algo_class.load(random_model_path, env=env)
    obs, _ = env.reset()
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        env.render()
    env.close()

    # Continue with best model as before...
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