import gymnasium as gym
import numpy as np
import pygame

# Import everything needed from your game
from multi_brick import (
    GAME_WIDTH, SCREEN_HEIGHT, PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED, BALL_RADIUS,
    Ball, Paddle, AIPaddle, Brick, PowerUp,
    create_bricks, reset_level,
    player_brick_stats, ai_brick_stats, player_balls_lost, ai_balls_lost,
    player_round_score, ai_round_score, player_total_score, ai_total_score,
    round_number, round_winner, showing_round_summary, round_summary_start_time,
    # If you use other globals, add them here
)

class BrickPongEnv(gym.Env):
    """
    Gym wrapper for Ultimate Brick Pong.
    The agent controls the player paddle (bottom). AI is heuristic.
    Observation: [player_x, ai_x, for each ball: x, y, vx, vy (up to max_balls)]
    Action: 0 = stay, 1 = left, 2 = right
    Reward: +1 for breaking a brick, -1 for losing a ball, 0 otherwise.
    """
    metadata = {"render.modes": ["human"]}

    def __init__(self, max_balls=6, rl_mode=True):
        super().__init__()
        self.max_balls = max_balls
        self.rl_mode = rl_mode

        # Action space: 0 = stay, 1 = left, 2 = right
        self.action_space = gym.spaces.Discrete(3)

        # Observation: player_x, ai_x, for each ball: x, y, vx, vy (pad to max_balls)
        low = np.array([0, 0] + [0, 0, -20, -20] * max_balls, dtype=np.float32)
        high = np.array([GAME_WIDTH, GAME_WIDTH] + [GAME_WIDTH, SCREEN_HEIGHT, 20, 20] * max_balls, dtype=np.float32)
        self.observation_space = gym.spaces.Box(low, high, dtype=np.float32)

        pygame.init()
        if self.rl_mode:
            self.screen = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT))
        else:
            self.screen = pygame.display.set_mode((GAME_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self._setup_game()

    def _setup_game(self):
        # Create paddles
        self.player_paddle = Paddle((GAME_WIDTH - PADDLE_WIDTH) // 2, SCREEN_HEIGHT - 60)
        self.ai_paddle = AIPaddle((GAME_WIDTH - PADDLE_WIDTH) // 2, 40)
        self.level = 1
        self.score = 0
        self.done = False
        self.reset()

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        # Reset the game state using your game's reset_level function
        reset_level(self.player_paddle, self.ai_paddle, self.level)
        # Sync global state to local
        from multi_brick import balls, bricks, player_balls_lost, ai_balls_lost
        self.balls = balls
        self.bricks = bricks
        self.player_balls_lost = player_balls_lost
        self.ai_balls_lost = ai_balls_lost
        self.done = False
        obs = self._get_obs()
        info = {}  # Optionally add info
        return obs, info

    def step(self, action):
        # --- Apply agent action ---
        if action == 1:
            self.player_paddle.move(-PADDLE_SPEED)
        elif action == 2:
            self.player_paddle.move(PADDLE_SPEED)

        # --- AI action (heuristic) ---
        self.ai_paddle.update(self.balls)

        # --- Ball update and collision ---
        reward = 0
        for ball in self.balls[:]:
            ball.update()
            # Ball lost (bottom)
            if ball.rect.bottom >= SCREEN_HEIGHT:
                self.player_balls_lost += 1
                self.balls.remove(ball)
                reward -= 1
            # Ball lost (top)
            elif ball.rect.top <= 0:
                self.ai_balls_lost += 1
                self.balls.remove(ball)
            # Paddle collision
            if ball.rect.colliderect(self.player_paddle.rect) and ball.vy > 0:
                ball.vy = -abs(ball.vy)
                offset = (ball.rect.centerx - self.player_paddle.rect.centerx) / (self.player_paddle.rect.width / 2)
                ball.vx = 5 * offset * 1.5
                ball.rect.bottom = self.player_paddle.rect.top
                ball.last_hit_by = "player"
            if ball.rect.colliderect(self.ai_paddle.rect) and ball.vy < 0:
                ball.vy = abs(ball.vy)
                offset = (ball.rect.centerx - self.ai_paddle.rect.centerx) / (self.ai_paddle.rect.width / 2)
                ball.vx = 5 * offset * 1.5
                ball.rect.top = self.ai_paddle.rect.bottom
                ball.last_hit_by = "ai"
            # Brick collision
            for brick in self.bricks[:]:
                if ball.rect.colliderect(brick.rect):
                    if brick.hit():
                        self.bricks.remove(brick)
                        if ball.last_hit_by == "player":
                            reward += 1
                    ball.vy = -ball.vy
                    break

        # --- Done? ---
        terminated = len(self.balls) == 0 or len(self.bricks) == 0 or self.player_balls_lost >= 5
        truncated = False  # You can add a max steps limit if you want
        info = {"winner": "agent" if len(self.bricks) == 0 else "env"}
        return self._get_obs(), reward, terminated, truncated, info

    def _get_obs(self):
        # Observation: player_x, ai_x, for each ball: x, y, vx, vy (pad to max_balls)
        obs = [self.player_paddle.rect.centerx, self.ai_paddle.rect.centerx]
        for i in range(self.max_balls):
            if i < len(self.balls):
                b = self.balls[i]
                obs.extend([b.rect.centerx, b.rect.centery, b.vx, b.vy])
            else:
                obs.extend([0, 0, 0, 0])
        return np.array(obs, dtype=np.float32)

    def render(self, mode="human"):
        if not self.rl_mode:
            # --- Full rendering for demo/video ---
            self.screen.fill((30, 30, 40))

            # Draw AI paddle with glow
            pygame.draw.rect(self.screen, (255, 200, 200), pygame.Rect(
                self.ai_paddle.rect.x - 2,
                self.ai_paddle.rect.y - 2,
                self.ai_paddle.rect.width + 4,
                self.ai_paddle.rect.height + 4
            ), 2)

            # Draw player paddle with glow
            pygame.draw.rect(self.screen, (200, 255, 200), pygame.Rect(
                self.player_paddle.rect.x - 2,
                self.player_paddle.rect.y - 2,
                self.player_paddle.rect.width + 4,
                self.player_paddle.rect.height + 4
            ), 2)

            # Draw paddles
            pygame.draw.rect(self.screen, (255, 100, 100), self.ai_paddle.rect)
            pygame.draw.rect(self.screen, (100, 255, 100), self.player_paddle.rect)

            # Draw bricks
            for brick in self.bricks:
                pygame.draw.rect(self.screen, brick.color, brick.rect)
                if hasattr(brick, "special") and brick.special:
                    pygame.draw.rect(self.screen, (255, 255, 0), brick.rect, 2)

            # Draw balls with trail effect
            for ball in self.balls:
                # Draw trail
                if hasattr(ball, "trail") and ball.trail:
                    for i, trail_pos in enumerate(ball.trail[-3:][::-1]):
                        trail_radius = max(1, ball.rect.width // 2 - i)
                        alpha = 255 - i * 60
                        trail_color = (255, 255, 255, alpha)
                        trail_surface = pygame.Surface((trail_radius*2, trail_radius*2), pygame.SRCALPHA)
                        pygame.draw.circle(trail_surface, trail_color, (trail_radius, trail_radius), trail_radius)
                        self.screen.blit(trail_surface, (trail_pos[0] - trail_radius, trail_pos[1] - trail_radius))
                # Draw main ball
                pygame.draw.ellipse(self.screen, (255, 255, 255), ball.rect)
                # Ball glow
                glow_rect = pygame.Rect(
                    ball.rect.x - 3,
                    ball.rect.y - 3,
                    ball.rect.width + 6,
                    ball.rect.height + 6
                )
                glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.ellipse(glow_surface, (200, 200, 255, 100), glow_surface.get_rect(), 2)
                self.screen.blit(glow_surface, (glow_rect.x, glow_rect.y))

            # Draw side panel with metrics (if you have a function for this)
            if "draw_side_panel" in globals():
                font = pygame.font.SysFont("Arial", 18)
                metrics = {
                    "player_score": getattr(self, "score", 0),
                    "ai_score": getattr(self, "ai_score", 0),
                    "level": getattr(self, "level", 1),
                    # Add more metrics as needed
                }
                draw_side_panel(self.screen, font, metrics)

            pygame.display.flip()

    def close(self):
        pygame.quit()