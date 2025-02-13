import pygame
import numpy as np
from collections import deque
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
import random

# ---------------------------- CONSTANTS ----------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Paddle properties
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_SPEED = 7

# Ball properties
BALL_RADIUS = 10
INITIAL_BALL_SPEED = 5

# Brick properties
BRICK_ROWS = 6
BRICK_COLS = 10
BRICK_WIDTH = 70
BRICK_HEIGHT = 30
BRICK_GAP = 5

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
BLUE  = (0, 0, 255)
GRAY  = (200, 200, 200)

# ---------------------------- CLASSES ----------------------------
class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model()
    
    def _build_model(self):
        model = models.Sequential()
        model.add(layers.Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(layers.Dense(24, activation='relu'))
        model.add(layers.Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=optimizers.Adam(learning_rate=self.learning_rate))
        return model
    
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        state = np.reshape(state, [1, self.state_size])
        act_values = self.model.predict(state, verbose=0)
        return np.argmax(act_values[0])
    
    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                next_state = np.reshape(next_state, [1, self.state_size])
                target = reward + self.gamma * np.amax(self.model.predict(next_state, verbose=0)[0])
            state = np.reshape(state, [1, self.state_size])
            target_f = self.model.predict(state, verbose=0)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def save_model(self, filename):
        self.model.save_weights(filename)


class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)

    def move(self, dx):
        self.rect.x += dx
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

class AIPaddle(Paddle):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.state_size = 5  # [ball_x, ball_y, ball_vx, ball_vy, paddle_x]
        self.action_size = 3  # 0:left, 1:stay, 2:right
        self.agent = DQNAgent(self.state_size, self.action_size)
        self.last_state = None
        self.last_action = None
        self.current_reward = 0
        self.total_reward = 0

    def get_state(self, balls):
        if not balls:
            return np.zeros(self.state_size)
        closest_ball = min(balls, key=lambda b: abs(b.rect.centery - self.rect.centery))
        return np.array([
            closest_ball.rect.centerx / SCREEN_WIDTH,
            closest_ball.rect.centery / SCREEN_HEIGHT,
            closest_ball.vx / INITIAL_BALL_SPEED,
            closest_ball.vy / INITIAL_BALL_SPEED,
            self.rect.centerx / SCREEN_WIDTH
        ])
    
    def update(self, balls, done):
        state = self.get_state(balls)
        
        if self.last_state is not None:
            self.agent.remember(self.last_state, self.last_action, 
                              self.current_reward, state, done)
        
        action = self.agent.act(state)
        self.last_state = state
        self.last_action = action
        
        # Take action
        if action == 0:
            self.move(-PADDLE_SPEED)
        elif action == 2:
            self.move(PADDLE_SPEED)
            
        self.current_reward = 0  # Reset reward after recording

class Ball:
    def __init__(self, x, y):
        # The ball's position is stored in a Rect for simplicity.
        self.rect = pygame.Rect(x, y, BALL_RADIUS * 2, BALL_RADIUS * 2)
        self.vx = random.choice([-1, 1]) * INITIAL_BALL_SPEED
        # Launch upward if starting from the bottom paddle, downward if from the top.
        self.vy = -INITIAL_BALL_SPEED if y > SCREEN_HEIGHT / 2 else INITIAL_BALL_SPEED

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

class Brick:
    def __init__(self, x, y, brick_type):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
        self.type = brick_type
        # Define brick properties based on type:
        # Type 1: normal brick (1 hit), Type 2: hard brick (3 hits), Type 3: permanent brick (never breaks)
        if brick_type == 1:
            self.hits = 1
            self.color = BLUE
        elif brick_type == 2:
            self.hits = 3
            self.color = RED
        elif brick_type == 3:
            self.hits = -1  # indicates an unbreakable brick
            self.color = GRAY

    def hit(self):
        if self.hits > 0:
            self.hits -= 1
            if self.hits == 0:
                return True  # brick should be removed
            else:
                # Darken the color slightly to indicate damage (simple approach)
                self.color = (max(self.color[0]-50, 0),
                              max(self.color[1]-50, 0),
                              max(self.color[2]-50, 0))
        return False

# ---------------------------- HELPER FUNCTIONS ----------------------------
def create_bricks():
    bricks = []
    # Center the brick grid horizontally
    total_width = BRICK_COLS * BRICK_WIDTH + (BRICK_COLS - 1) * BRICK_GAP
    offset_x = (SCREEN_WIDTH - total_width) // 2
    offset_y = 50  # start a bit from the top
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            if random.random() < 0.7:  # 70% chance to place a brick
                x = offset_x + col * (BRICK_WIDTH + BRICK_GAP)
                y = offset_y + row * (BRICK_HEIGHT + BRICK_GAP)
                # Randomly choose a brick type with weights: 50% normal, 30% hard, 20% permanent
                brick_type = random.choices([1, 2, 3], weights=[50, 30, 20])[0]
                bricks.append(Brick(x, y, brick_type))
    return bricks

def reset_level():
    """Resets the ball list to a single ball (from the player’s paddle) and regenerates the brick layout."""
    global balls, last_ball_mult_time, bricks
    # Position the new ball above the player's paddle
    balls = [Ball(player_paddle.rect.centerx - BALL_RADIUS, player_paddle.rect.top - BALL_RADIUS * 2)]
    last_ball_mult_time = pygame.time.get_ticks()
    bricks = create_bricks()

# ---------------------------- MAIN GAME LOOP ----------------------------
def main():
    global player_paddle, balls, bricks, last_ball_mult_time

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Brick Versus")
    clock = pygame.time.Clock()

    # Load sound effects (ensure these files are available in your working directory)
    try:
        hit_sound = pygame.mixer.Sound("hit.wav")
        brick_sound = pygame.mixer.Sound("brick.wav")
        lost_sound = pygame.mixer.Sound("lost.wav")
    except Exception as e:
        print("Sound files not found or could not be loaded; continuing without sound.")
        hit_sound = brick_sound = lost_sound = None

    # Create player and AI paddles
    global player_paddle  # used by reset_level
    player_paddle = Paddle((SCREEN_WIDTH - PADDLE_WIDTH) // 2, SCREEN_HEIGHT - 40)
    ai_paddle = AIPaddle((SCREEN_WIDTH - PADDLE_WIDTH) // 2, 20)

    # Training parameters
    training = True  # Set to False to disable training
    batch_size = 32
    total_episodes = 0
    model_save_path = "brick_breaker_rl.h5"

    # Initialize game state
    player_lives = 3
    ai_lives = 3
    score = 0

    # Start with one ball and create the initial brick layout.
    balls = [Ball(player_paddle.rect.centerx - BALL_RADIUS, player_paddle.rect.top - BALL_RADIUS * 2)]
    bricks = create_bricks()
    last_ball_mult_time = pygame.time.get_ticks()
    ball_mult_interval = 15000  # milliseconds between ball multiplications

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # ---------------------------- PLAYER INPUT ----------------------------
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_paddle.move(-PADDLE_SPEED)
        if keys[pygame.K_RIGHT]:
            player_paddle.move(PADDLE_SPEED)

        # ---------------------------- AI UPDATE ----------------------------
        ai_done = False
        # Calculate reward
        ai_paddle.current_reward = -0.1  # Small penalty per frame
        
        # Check for ball collisions with AI paddle
        for ball in balls:
            if ball.rect.colliderect(ai_paddle.rect):
                ai_paddle.current_reward += 2  # Positive reward for hitting
        
        # Check for missed balls
        if any(ball.rect.top <= 0 for ball in balls):
            ai_paddle.current_reward -= 10  # Big penalty for missing
            ai_done = True

        ai_paddle.update(balls, ai_done)
        
        # Experience replay
        if training and len(ai_paddle.agent.memory) > batch_size:
            ai_paddle.agent.replay(batch_size)

        # ---------------------------- UPDATE BALLS ----------------------------
        # Iterate over a copy of the list since we may reset mid-loop
        for ball in balls:
            ball.update()

            # Collision with side walls
            if ball.rect.left <= 0 or ball.rect.right >= SCREEN_WIDTH:
                ball.vx = -ball.vx
                if hit_sound:
                    hit_sound.play()

            # Check if ball goes off the top or bottom
            if ball.rect.top <= 0:
                # Ball missed by the AI paddle – AI loses a life.
                ai_lives -= 1
                if lost_sound:
                    lost_sound.play()
                reset_level()
                break  # break out of the ball loop to avoid multiple life losses
            if ball.rect.bottom >= SCREEN_HEIGHT:
                # Ball missed by the player – player loses a life.
                player_lives -= 1
                if lost_sound:
                    lost_sound.play()
                reset_level()
                break

            # Collision with player paddle (only when the ball is moving downward)
            if ball.rect.colliderect(player_paddle.rect) and ball.vy > 0:
                ball.vy = -abs(ball.vy)
                # Adjust horizontal speed based on where the ball hit the paddle.
                offset = (ball.rect.centerx - player_paddle.rect.centerx) / (PADDLE_WIDTH / 2)
                ball.vx = INITIAL_BALL_SPEED * offset
                if hit_sound:
                    hit_sound.play()

            # Collision with AI paddle (only when the ball is moving upward)
            if ball.rect.colliderect(ai_paddle.rect) and ball.vy < 0:
                ball.vy = abs(ball.vy)
                offset = (ball.rect.centerx - ai_paddle.rect.centerx) / (PADDLE_WIDTH / 2)
                ball.vx = INITIAL_BALL_SPEED * offset
                if hit_sound:
                    hit_sound.play()

            # Collision with bricks
            for brick in bricks[:]:
                if ball.rect.colliderect(brick.rect):
                    # A simple collision response: reverse the vertical direction.
                    ball.vy = -ball.vy
                    if brick_sound:
                        brick_sound.play()
                    if brick.hit():
                        bricks.remove(brick)
                        score += 10
                    break  # avoid multiple collisions for one ball in a single frame

        # ---------------------------- BALL MULTIPLICATION ----------------------------
        current_time = pygame.time.get_ticks()
        if current_time - last_ball_mult_time > ball_mult_interval:
            # For each current ball, spawn an extra ball with a slight variation.
            new_balls = []
            for ball in balls:
                new_ball = Ball(ball.rect.x, ball.rect.y)
                new_ball.vx = -ball.vx  # Invert x-velocity to vary the trajectory.
                new_ball.vy = ball.vy
                new_balls.append(new_ball)
            balls.extend(new_balls)
            last_ball_mult_time = current_time

        # ---------------------------- DRAWING ----------------------------
        screen.fill(BLACK)

        # Draw bricks
        for brick in bricks:
            pygame.draw.rect(screen, brick.color, brick.rect)

        # Draw paddles
        pygame.draw.rect(screen, WHITE, player_paddle.rect)
        pygame.draw.rect(screen, WHITE, ai_paddle.rect)

        # Draw balls
        for ball in balls:
            pygame.draw.ellipse(screen, WHITE, ball.rect)

        # Draw scoreboard (score and lives)
        font = pygame.font.SysFont("Arial", 20)
        score_text = font.render(f"Score: {score}", True, WHITE)
        lives_text = font.render(f"Player Lives: {player_lives}   AI Lives: {ai_lives}", True, WHITE)
        screen.blit(score_text, (10, SCREEN_HEIGHT - 30))
        screen.blit(lives_text, (10, SCREEN_HEIGHT - 60))

        pygame.display.flip()

        # ---------------------------- GAME OVER CHECK ----------------------------
        if player_lives <= 0 or ai_lives <= 0:
            if training:
                ai_paddle.agent.save_model(model_save_path)
                print(f"Model saved to {model_save_path}")
            running = False

    # Display a game over message.
    screen.fill(BLACK)
    game_over_text = font.render("Game Over!", True, WHITE)
    screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.quit()

if __name__ == "__main__":
    main()
