import os
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import DQN, PPO, A2C, SAC
from stable_baselines3.common.evaluation import evaluate_policy
from brickpong_gym_env import BrickPongEnv

# Directory to save models and results
MODEL_DIR = "rl_models"
os.makedirs(MODEL_DIR, exist_ok=True)

# RL algorithms to compare
algorithms = {
    "DQN": DQN,
    "PPO": PPO,
    "A2C": A2C,
    "SAC": SAC
}

results = {}
NUM_TRAIN_STEPS = 50_000  # You can increase for better results
NUM_EVAL_EPISODES = 20

for algo_name, algo_class in algorithms.items():
    print(f"\n=== Training {algo_name} ===")
    env = BrickPongEnv()
    # SAC requires continuous action space, so we skip it if not supported
    if algo_name == "SAC" and not hasattr(env.action_space, "n"):
        print("Skipping SAC (requires continuous action space)")
        continue
    model = algo_class("MlpPolicy", env, verbose=0)
    model.learn(total_timesteps=NUM_TRAIN_STEPS)
    model.save(os.path.join(MODEL_DIR, f"{algo_name}_model"))
    print(f"Evaluating {algo_name}...")
    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=NUM_EVAL_EPISODES, return_episode_rewards=False)
    episode_rewards = []
    win_count = 0
    for _ in range(NUM_EVAL_EPISODES):
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
    results[algo_name] = {
        "rewards": episode_rewards,
        "mean_reward": np.mean(episode_rewards),
        "win_rate": win_count / NUM_EVAL_EPISODES
    }
    print(f"{algo_name}: Mean Reward = {results[algo_name]['mean_reward']:.2f}, Win Rate = {results[algo_name]['win_rate']:.2f}")

# Plotting results
plt.figure(figsize=(10, 6))
for algo_name in results:
    plt.plot(results[algo_name]["rewards"], label=f"{algo_name} (win rate: {results[algo_name]['win_rate']:.2f})")
plt.xlabel("Evaluation Episode")
plt.ylabel("Total Reward")
plt.title("RL Algorithm Comparison: Rewards per Episode")
plt.legend()
plt.tight_layout()
plt.savefig("rl_algorithms_rewards.png")
plt.show()

# Bar plot for win rates
plt.figure(figsize=(8, 5))
win_rates = [results[algo]["win_rate"] for algo in results]
plt.bar(list(results.keys()), win_rates, color='skyblue')
plt.ylabel("Win Rate")
plt.title("RL Algorithm Comparison: Win Rates")
plt.tight_layout()
plt.savefig("rl_algorithms_winrates.png")
plt.show()

print("Training and evaluation complete. Models and plots saved.")