import gym
import numpy as np
import os
from gym import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
import torch

# --------------------- ENVIRONMENT SETUP ---------------------
class PaddleEnv(gym.Env):
    """ Custom Gym environment for Paddle movement in Brick Breaker. """
    
    def __init__(self):
        super(PaddleEnv, self).__init__()

        # Game settings
        self.GAME_WIDTH = 1200
        self.GAME_HEIGHT = 800
        self.PADDLE_WIDTH = 100
        self.PADDLE_HEIGHT = 20
        self.BALL_RADIUS = 10
        self.PADDLE_SPEED = 20
        self.BALL_SPEED = 5
        
        # Observation Space (paddle x, ball x, ball y, ball vx, ball vy)
        self.observation_space = spaces.Box(low=np.array([0, 0, 0, -self.BALL_SPEED, -self.BALL_SPEED]),
                                            high=np.array([self.GAME_WIDTH, self.GAME_WIDTH, self.GAME_HEIGHT, self.BALL_SPEED, self.BALL_SPEED]),
                                            dtype=np.float32)

        # Action Space (Discrete: 0 = Left, 1 = Stay, 2 = Right)
        self.action_space = spaces.Discrete(3)

        self.reset()

    def reset(self):
        """ Reset the environment state. """
        self.paddle_x = self.GAME_WIDTH // 2
        self.ball_x = np.random.randint(self.BALL_RADIUS, self.GAME_WIDTH - self.BALL_RADIUS)
        self.ball_y = np.random.randint(self.GAME_HEIGHT // 2, self.GAME_HEIGHT - 50)
        self.ball_vx = np.random.choice([-1, 1]) * self.BALL_SPEED
        self.ball_vy = -self.BALL_SPEED  # Ball moving upwards

        return self._get_state()

    def _get_state(self):
        """ Get the current state as a NumPy array. """
        return np.array([self.paddle_x, self.ball_x, self.ball_y, self.ball_vx, self.ball_vy], dtype=np.float32)

    def step(self, action):
        """ Take an action and return (next_state, reward, done, info). """
        if action == 0:  # Move left
            self.paddle_x = max(0, self.paddle_x - self.PADDLE_SPEED)
        elif action == 2:  # Move right
            self.paddle_x = min(self.GAME_WIDTH, self.paddle_x + self.PADDLE_SPEED)

        # Move ball
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        # Ball-wall collision
        if self.ball_x <= self.BALL_RADIUS or self.ball_x >= self.GAME_WIDTH - self.BALL_RADIUS:
            self.ball_vx = -self.ball_vx  # Reflect ball horizontally

        # Ball hits paddle
        reward = 0
        done = False
        if self.ball_y >= self.GAME_HEIGHT - 50:  # Paddle region
            if abs(self.paddle_x - self.ball_x) <= self.PADDLE_WIDTH // 2:
                self.ball_vy = -self.ball_vy  # Reflect ball
                reward = 1  # Positive reward for hitting the ball
            else:
                reward = -1  # Penalty for missing
                done = True  # Game over (ball missed)

        return self._get_state(), reward, done, {}

    def render(self, mode="human"):
        pass  # Can add visualization if needed

# --------------------- TRAINING SETUP ---------------------
# Create environment
env = PaddleEnv()

# Define model save path
MODEL_DIR = "ppo_models"
os.makedirs(MODEL_DIR, exist_ok=True)

# Check if CUDA is available
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Callback to save model checkpoints
checkpoint_callback = CheckpointCallback(save_freq=10_000, save_path=MODEL_DIR, name_prefix="brick_rl")

# Train PPO model with CUDA support
model = PPO("MlpPolicy", env, verbose=1, learning_rate=0.0003, n_steps=2048, batch_size=64, gamma=0.99, device=device)
model.learn(total_timesteps=200_000, callback=checkpoint_callback)

# Save the final model
model.save(os.path.join(MODEL_DIR, "ppo_paddle"))

print("Training complete! Model saved in:", MODEL_DIR)
