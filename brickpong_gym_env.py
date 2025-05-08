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
        self.max_powerups = 3
        self.max_bricks = 20  # Pad to 20 bricks for obs
        self.rl_mode = rl_mode

        # Observation: 
        # [player_x, ai_x, player_left, player_right, ai_left, ai_right]
        # For each ball: x, y, vx, vy, dist_to_paddle, dist_to_nearest_brick (6×6=36)
        # Closest ball dx, dy
        # Balls left, bricks left
        # For each brick: x, y, type (20×3=60)
        # For each powerup: x, y, type (3×3=9)
        obs_len = 6 + self.max_balls*6 + 2 + 2 + self.max_bricks*3 + self.max_powerups*3

        low = np.full(obs_len, -1000, dtype=np.float32)
        high = np.full(obs_len, 2000, dtype=np.float32)
        self.observation_space = gym.spaces.Box(low, high, dtype=np.float32)

        self.action_space = gym.spaces.Discrete(3)

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
        self.player_bricks_broken = 0
        self.ai_bricks_broken = 0
        self.done = False
        obs = self._get_obs()
        info = {}  # Optionally add info
        return obs, info

    def step(self, action):
        prev_x = self.player_paddle.rect.centerx
        reward = 0.0  # Initialize reward FIRST
        
        # Move paddle
        if action == 1:
            self.player_paddle.move(-PADDLE_SPEED)
        elif action == 2:
            self.player_paddle.move(PADDLE_SPEED)

        # Add movement incentive
        if abs(prev_x - self.player_paddle.rect.centerx) > 0:
            reward += 0.05  # Stronger incentive to move

        self.ai_paddle.update(self.balls)

        # Penalize hugging the wall
        if self.player_paddle.rect.left <= 0 or self.player_paddle.rect.right >= GAME_WIDTH:
            reward -= 0.01

        # Encourage movement
        if not hasattr(self, "no_move_steps"):
            self.no_move_steps = 0
        if self.player_paddle.rect.centerx != prev_x:
            reward += 0.01
            self.no_move_steps = 0
        else:
            self.no_move_steps += 1
            if self.no_move_steps >= 10:
                reward -= 0.05  # Penalize standing still

        # Track bricks broken this step
        bricks_broken_this_step = 0

        for ball in self.balls[:]:
            ball.update()
            # Ball lost (bottom)
            if ball.rect.bottom >= SCREEN_HEIGHT:
                self.player_balls_lost += 1
                self.balls.remove(ball)
                reward -= 10.0
                continue

            # Ball lost (top)
            elif ball.rect.top <= 0:
                self.ai_balls_lost += 1
                self.balls.remove(ball)
                continue

            # Paddle collision (player)
            if ball.rect.colliderect(self.player_paddle.rect) and ball.vy > 0:
                ball.vy = -abs(ball.vy)
                offset = (ball.rect.centerx - self.player_paddle.rect.centerx) / (self.player_paddle.rect.width / 2)
                ball.vx = 5 * offset * 1.5
                ball.rect.bottom = self.player_paddle.rect.top
                ball.last_hit_by = "player"
                reward += 0.1
                reward += 0.5  # Bigger reward for hitting the ball

            # Paddle collision (AI)
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
                            reward += 1.0
                            bricks_broken_this_step += 1
                    ball.vy = -ball.vy
                    break

        # Bonus for breaking multiple bricks in one step
        if bricks_broken_this_step > 1:
            reward += 0.5 * (bricks_broken_this_step - 1)

        terminated = len(self.balls) == 0 or len(self.bricks) == 0 or self.player_balls_lost >= 5 or getattr(self, "done", False)
        truncated = False
        info = {
            "winner": "agent" if len(self.bricks) == 0 else "env",
            "balls_left": len(self.balls),
            "bricks_left": len(self.bricks),
            "player_balls_lost": self.player_balls_lost,
        }
        return self._get_obs(), reward, terminated, truncated, info

    def _get_obs(self):
        obs = []
        # Paddle positions and edges
        obs.extend([
            self.player_paddle.rect.centerx,
            self.ai_paddle.rect.centerx,
            self.player_paddle.rect.left,
            self.player_paddle.rect.right,
            self.ai_paddle.rect.left,
            self.ai_paddle.rect.right,
        ])
        # Balls
        for i in range(self.max_balls):
            if i < len(self.balls):
                b = self.balls[i]
                # Distance to player paddle center
                dist_to_paddle = np.linalg.norm([
                    b.rect.centerx - self.player_paddle.rect.centerx,
                    b.rect.centery - self.player_paddle.rect.centery
                ])
                # Distance to nearest brick
                if self.bricks:
                    dists = [np.linalg.norm([
                        b.rect.centerx - brick.rect.centerx,
                        b.rect.centery - brick.rect.centery
                    ]) for brick in self.bricks]
                    dist_to_brick = min(dists)
                else:
                    dist_to_brick = 0
                obs.extend([
                    b.rect.centerx, b.rect.centery, b.vx, b.vy,
                    dist_to_paddle, dist_to_brick
                ])
            else:
                obs.extend([0, 0, 0, 0, 0, 0])
        # Closest ball dx/dy
        closest_ball_dx = 0
        closest_ball_dy = 0
        min_dist = float("inf")
        for b in self.balls:
            dx = b.rect.centerx - self.player_paddle.rect.centerx
            dy = b.rect.centery - self.player_paddle.rect.centery
            dist = abs(dx) + abs(dy)
            if dist < min_dist:
                min_dist = dist
                closest_ball_dx = dx
                closest_ball_dy = dy
        obs.extend([closest_ball_dx, closest_ball_dy])
        # Balls left, bricks left
        obs.append(len(self.balls))
        obs.append(len(self.bricks))
        # Bricks info (pad to max_bricks)
        for i in range(self.max_bricks):
            if i < len(self.bricks):
                brick = self.bricks[i]
                obs.extend([brick.rect.centerx, brick.rect.centery, getattr(brick, "type", -1)])
            else:
                obs.extend([0, 0, -1])
        # Powerups info (already padded in original)
        powerup_type_map = {"speed": 0, "size": 1, "multi": 2, "score": 3, "laser": 4, "slow": 5}
        powerups = getattr(self, "power_ups", [])
        for i in range(self.max_powerups):
            if i < len(powerups):
                pu = powerups[i]
                obs.extend([pu.rect.centerx, pu.rect.centery, powerup_type_map.get(pu.type, -1)])
            else:
                obs.extend([0, 0, -1])
        return np.array(obs, dtype=np.float32)

    def render(self, mode="human"):
        if not self.rl_mode:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                    pygame.quit()
                    return
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