import pygame
import numpy as np
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
    """
    A simple AI that tracks the closest ball horizontally.
    """
    def __init__(self, x, y):
        super().__init__(x, y)

    def update(self, balls):
        if balls:
            # Choose the ball that is closest vertically to the AI paddle
            closest_ball = min(balls, key=lambda b: abs(b.rect.centery - self.rect.centery))
            # Move towards the ball's x position
            if closest_ball.rect.centerx < self.rect.centerx:
                self.move(-PADDLE_SPEED)
            elif closest_ball.rect.centerx > self.rect.centerx:
                self.move(PADDLE_SPEED)

class Ball:
    def __init__(self, x, y):
        # Create a rect for collision simplicity
        self.rect = pygame.Rect(x, y, BALL_RADIUS * 2, BALL_RADIUS * 2)
        self.vx = random.choice([-1, 1]) * INITIAL_BALL_SPEED
        # If the ball spawns from the bottom (player side), launch upward.
        self.vy = -INITIAL_BALL_SPEED if y > SCREEN_HEIGHT / 2 else INITIAL_BALL_SPEED

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

class Brick:
    def __init__(self, x, y, brick_type):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
        self.type = brick_type
        # Brick types:
        # 1: normal brick (1 hit), 2: hard brick (3 hits), 3: permanent brick (never breaks)
        if brick_type == 1:
            self.hits = 1
            self.color = BLUE
        elif brick_type == 2:
            self.hits = 3
            self.color = RED
        elif brick_type == 3:
            self.hits = -1  # unbreakable
            self.color = GRAY

    def hit(self):
        if self.hits > 0:
            self.hits -= 1
            if self.hits == 0:
                return True  # remove brick
            else:
                # Darken the color a bit to indicate damage
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
    offset_y = 50  # some offset from the top
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
    """Reset the ball list to a single ball and regenerate the brick layout."""
    global balls, bricks, last_ball_mult_time
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

    # Load sound effects (make sure these files are in your working directory)
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

    player_lives = 3
    ai_lives = 3
    score = 0

    # Initialize ball and brick layout
    balls = [Ball(player_paddle.rect.centerx - BALL_RADIUS, player_paddle.rect.top - BALL_RADIUS * 2)]
    bricks = create_bricks()
    last_ball_mult_time = pygame.time.get_ticks()
    ball_mult_interval = 30000  # milliseconds between ball multiplications (30 seconds)

    font = pygame.font.SysFont("Arial", 20)

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
        ai_paddle.update(balls)

        # ---------------------------- UPDATE BALLS ----------------------------
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
                break  # exit ball loop to avoid multiple losses
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
                    ball.vy = -ball.vy  # simple vertical bounce
                    if brick_sound:
                        brick_sound.play()
                    if brick.hit():
                        bricks.remove(brick)
                        score += 10
                    break  # prevent multiple collisions in one update

        # ---------------------------- BALL MULTIPLICATION ----------------------------
        current_time = pygame.time.get_ticks()
        if current_time - last_ball_mult_time > ball_mult_interval:
            new_balls = []
            for ball in balls:
                new_ball = Ball(ball.rect.x, ball.rect.y)
                new_ball.vx = -ball.vx  # Invert x-velocity to vary the trajectory
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
        score_text = font.render(f"Score: {score}", True, WHITE)
        lives_text = font.render(f"Player Lives: {player_lives}   AI Lives: {ai_lives}", True, WHITE)
        screen.blit(score_text, (10, SCREEN_HEIGHT - 30))
        screen.blit(lives_text, (10, SCREEN_HEIGHT - 60))

        # Draw ball multiplication timer
        time_remaining = max(0, (ball_mult_interval - (current_time - last_ball_mult_time)) / 1000)
        timer_text = font.render(f"Balls multiply in: {time_remaining:.1f}s", True, WHITE)
        screen.blit(timer_text, (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 30))

        pygame.display.flip()

        # ---------------------------- GAME OVER CHECK ----------------------------
        if player_lives <= 0 or ai_lives <= 0:
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
