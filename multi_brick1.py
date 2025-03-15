import pygame
import random
import time
import numpy as np
from stable_baselines3 import PPO
import torch

# ---------------------------- DIMENSIONS ----------------------------
GAME_WIDTH = 1200
SIDE_WIDTH = 400
SCREEN_WIDTH = GAME_WIDTH + SIDE_WIDTH  # Total width (game area + side panel)
SCREEN_HEIGHT = 800
FPS = 60

# Paddle properties
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_SPEED = 20  # Increased speed

# Ball properties
BALL_RADIUS = 10
INITIAL_BALL_SPEED = 5

# ---------------------------- LOAD RL MODEL ----------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
model = PPO.load("ppo_models/ppo_paddle", device=device)
print(f"Loaded RL model on {device}")

# ---------------------------- CLASSES ----------------------------
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)

    def move(self, dx):
        self.rect.x += dx
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > GAME_WIDTH:
            self.rect.right = GAME_WIDTH

# AI Paddle using RL Model
class AIPaddle(Paddle):
    def __init__(self, x, y):
        super().__init__(x, y)

    def update(self, balls):
        """AI moves using the trained RL model's predictions."""
        if balls:
            # Get the closest ball
            closest_ball = min(balls, key=lambda b: abs(b.rect.centery - self.rect.centery))

            # Prepare the state representation for the model
            state = np.array([
                self.rect.centerx,  # Paddle x
                closest_ball.rect.centerx,  # Ball x
                closest_ball.rect.centery,  # Ball y
                closest_ball.vx,  # Ball vx
                closest_ball.vy   # Ball vy
            ], dtype=np.float32)

            # Get AI action from PPO model
            action, _ = model.predict(state, deterministic=True)

            # Apply the action (0 = Left, 1 = Stay, 2 = Right)
            if action == 0:
                self.move(-PADDLE_SPEED)
            elif action == 2:
                self.move(PADDLE_SPEED)

class Ball:
    def __init__(self, x, y, vy_direction):
        self.rect = pygame.Rect(x - BALL_RADIUS, y - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)
        self.vx = random.choice([-1, 1]) * INITIAL_BALL_SPEED
        self.vy = vy_direction * INITIAL_BALL_SPEED

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

        # Ball-wall collision
        if self.rect.left <= 0 or self.rect.right >= GAME_WIDTH:
            self.vx = -self.vx

# ---------------------------- GAME INITIALIZATION ----------------------------
def main():
    global balls

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Brick Breaker with RL AI")
    clock = pygame.time.Clock()

    # Initialize paddles
    player_paddle = Paddle((GAME_WIDTH - PADDLE_WIDTH) // 2, SCREEN_HEIGHT - 60)
    ai_paddle = AIPaddle((GAME_WIDTH - PADDLE_WIDTH) // 2, 40)

    # Initialize balls
    balls = [Ball(player_paddle.rect.centerx, player_paddle.rect.top - 20, -1)]

    running = True
    while running:
        dt = clock.tick(FPS)

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Player Input ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_paddle.move(-PADDLE_SPEED)
        if keys[pygame.K_RIGHT]:
            player_paddle.move(PADDLE_SPEED)

        # --- AI Update ---
        ai_paddle.update(balls)

        # --- Ball Updates ---
        for ball in balls:
            ball.update()

            # Collision with player paddle
            if ball.rect.colliderect(player_paddle.rect) and ball.vy > 0:
                ball.vy = -abs(ball.vy)

            # Collision with AI paddle
            if ball.rect.colliderect(ai_paddle.rect) and ball.vy < 0:
                ball.vy = abs(ball.vy)

        # --- Rendering ---
        screen.fill((30, 30, 30))  # Dark background
        pygame.draw.rect(screen, (255, 255, 255), player_paddle.rect)
        pygame.draw.rect(screen, (255, 0, 0), ai_paddle.rect)

        for ball in balls:
            pygame.draw.circle(screen, (255, 255, 255), (ball.rect.centerx, ball.rect.centery), BALL_RADIUS)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
