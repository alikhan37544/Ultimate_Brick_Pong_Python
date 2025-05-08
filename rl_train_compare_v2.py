import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import time
import multiprocessing

from stable_baselines3 import DQN, PPO, A2C
from sb3_contrib import QRDQN
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.vec_env import DummyVecEnv
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
    # Removed DDPG as it's for continuous action spaces
}

results = {}
NUM_TRAIN_STEPS = 50_000  # Increase for better learning
NUM_EVAL_EPISODES = 15
VIDEO_LENGTH = 500  # Steps to record for video

N_CPUS = multiprocessing.cpu_count()

def make_env():
    # Create environment without render_mode parameter
    return Monitor(BrickPongEnv(rl_mode=True))  # No rendering during training

def make_visual_env():
    # Create environment for visual evaluation/recording
    return Monitor(BrickPongEnv(rl_mode=False))  

def record_video(algo_name, model, video_length=VIDEO_LENGTH):
    # Only record video if explicitly needed - it's slow
    print(f"Recording video for {algo_name}...")
    
    # Create a visual environment for recording
    env = make_visual_env()
    video_path = os.path.join(VIDEO_DIR, f"{algo_name}_agent.mp4")
    
    # Initialize recording
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption(f"Recording {algo_name} Agent")
    
    obs, _ = env.reset()
    
    # Create a pygame.movie writer if available
    try:
        from pygame.movie import Movie
        movie = Movie(video_path, (1200, 800))
        movie_available = True
    except ImportError:
        movie_available = False
        print("pygame.movie not available. Recording frames as screenshots.")
        if not os.path.exists(VIDEO_DIR):
            os.makedirs(VIDEO_DIR)
    
    # Record steps
    for step in range(video_length):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        
        env.render()  # This will display the game
        pygame.display.flip()
        
        # Save frame if movie not available - only every 10th frame
        if not movie_available and step % 10 == 0:
            pygame.image.save(screen, os.path.join(VIDEO_DIR, f"{algo_name}_step_{step:04d}.png"))
        
        if done:
            obs, _ = env.reset()
    
    env.close()
    pygame.quit()
    print(f"Video recording completed for {algo_name}")

# Set this to True to see visual evaluation, False for maximum speed
RENDER_EVALUATION = True

# Set this to False to skip video recording for speed
RECORD_VIDEOS = True

# Main training and evaluation loop
plt.ion()  # Turn on interactive plotting mode
fig, axs = plt.subplots(2, 1, figsize=(10, 10))

for algo_name, algo_class in algorithms.items():
    print(f"\n=== Training {algo_name} ===")
    
    # Create a vectorized environment for training
    env = DummyVecEnv([make_env for _ in range(min(N_CPUS, 4))])  # Limit to 4 CPUs to avoid memory issues
    
    # Create and train the model
    model = algo_class("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=NUM_TRAIN_STEPS)
    
    # Save the trained model
    model_path = os.path.join(MODEL_DIR, f"{algo_name}_model")
    model.save(model_path)
    print(f"Model saved to {model_path}")
    
    # Evaluate the model
    print(f"Evaluating {algo_name}...")
    eval_env = make_visual_env()
    episode_rewards = []
    win_count = 0
    
    # Run evaluation episodes
    for _ in tqdm(range(NUM_EVAL_EPISODES), desc=f"Evaluating {algo_name}", ncols=80):
        obs, _ = eval_env.reset()
        done = False
        total_reward = 0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            
            obs, reward, terminated, truncated, info = eval_env.step(action)
            done = terminated or truncated
            total_reward += reward
            
            # Only render if explicitly requested
            if RENDER_EVALUATION:
                eval_env.render()
            
        episode_rewards.append(total_reward)
        if "winner" in info and info["winner"] == "agent":
            win_count += 1
    
    # Record a video of the trained agent (optional)
    if RECORD_VIDEOS:
        record_video(algo_name, model)
    
    # Store results
    results[algo_name] = {
        "rewards": episode_rewards,
        "mean_reward": np.mean(episode_rewards),
        "win_rate": win_count / NUM_EVAL_EPISODES
    }
    print(f"{algo_name}: Mean Reward = {results[algo_name]['mean_reward']:.2f}, Win Rate = {results[algo_name]['win_rate']:.2f}")
    
    # Update live plot
    axs[0].cla()
    for name in results:
        axs[0].plot(results[name]["rewards"], label=f"{name} (win rate: {results[name]['win_rate']:.2f})")
    axs[0].set_xlabel("Evaluation Episode")
    axs[0].set_ylabel("Total Reward")
    axs[0].set_title("RL Algorithm Comparison: Rewards per Episode")
    axs[0].legend()
    axs[0].grid(True)
    
    # Update win rate bars
    axs[1].cla()
    win_rates = [results[algo]["win_rate"] for algo in results]
    axs[1].bar(list(results.keys()), win_rates, color='skyblue')
    axs[1].set_ylabel("Win Rate")
    axs[1].set_title("RL Algorithm Comparison: Win Rates")
    axs[1].set_ylim(0, 1)
    axs[1].grid(axis='y')
    
    plt.tight_layout()
    plt.pause(0.1)
    plt.savefig(f"rl_comparison_progress_{len(results)}.png")

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