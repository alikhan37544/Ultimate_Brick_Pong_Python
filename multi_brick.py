import pygame
import numpy as np
import random

# ---------------------------- CONSTANTS ----------------------------
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Paddle properties
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_SPEED = 10  # increased speed

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
    def __init__(self, x, y):
        super().__init__(x, y)

    def update(self, balls):
        if balls:
            closest_ball = min(balls, key=lambda b: abs(b.rect.centery - self.rect.centery))
            if closest_ball.rect.centerx < self.rect.centerx:
                self.move(-PADDLE_SPEED)
            elif closest_ball.rect.centerx > self.rect.centerx:
                self.move(PADDLE_SPEED)

class Ball:
    def __init__(self, x, y, vy_direction):
        self.rect = pygame.Rect(x, y, BALL_RADIUS * 2, BALL_RADIUS * 2)
        self.vx = random.choice([-1, 1]) * INITIAL_BALL_SPEED
        self.vy = vy_direction * INITIAL_BALL_SPEED

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

class Brick:
    def __init__(self, x, y, brick_type):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
        self.type = brick_type
        if brick_type == 1:
            self.hits = 1
            self.color = BLUE
        elif brick_type == 2:
            self.hits = 3
            self.color = RED
        elif brick_type == 3:
            self.hits = -1
            self.color = GRAY

    def hit(self):
        if self.hits > 0:
            self.hits -= 1
            if self.hits == 0:
                return True
            else:
                self.color = (max(self.color[0]-50, 0),
                              max(self.color[1]-50, 0),
                              max(self.color[2]-50, 0))
        return False

# ---------------------------- HELPER FUNCTIONS ----------------------------
def create_bricks():
    bricks = []
    total_width = BRICK_COLS * BRICK_WIDTH + (BRICK_COLS - 1) * BRICK_GAP
    total_height = BRICK_ROWS * BRICK_HEIGHT + (BRICK_ROWS - 1) * BRICK_GAP
    offset_x = (SCREEN_WIDTH - total_width) // 2
    offset_y = (SCREEN_HEIGHT - total_height) // 2
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            if random.random() < 0.7:
                x = offset_x + col * (BRICK_WIDTH + BRICK_GAP)
                y = offset_y + row * (BRICK_HEIGHT + BRICK_GAP)
                brick_type = random.choices([1, 2, 3], weights=[50, 30, 20])[0]
                bricks.append(Brick(x, y, brick_type))
    return bricks

def reset_level(player_paddle, ai_paddle):
    global balls, bricks, last_ball_mult_time
    balls = []

    # Spawn only one ball for the player
    balls.append(Ball(player_paddle.rect.centerx, player_paddle.rect.top - BALL_RADIUS * 2, -1))

    # Spawn only one ball for the AI
    balls.append(Ball(ai_paddle.rect.centerx, ai_paddle.rect.bottom + BALL_RADIUS * 2, 1))

    last_ball_mult_time = pygame.time.get_ticks()
    bricks = create_bricks()

# ---------------------------- MAIN GAME LOOP ----------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Brick Versus")
    clock = pygame.time.Clock()

    try:
        hit_sound = pygame.mixer.Sound("hit.wav")
        brick_sound = pygame.mixer.Sound("brick.wav")
        lost_sound = pygame.mixer.Sound("lost.wav")
    except:
        print("Sound files not found or could not be loaded; continuing without sound.")
        hit_sound = brick_sound = lost_sound = None

    player_paddle = Paddle((SCREEN_WIDTH - PADDLE_WIDTH) // 2, SCREEN_HEIGHT - 60)
    ai_paddle = AIPaddle((SCREEN_WIDTH - PADDLE_WIDTH) // 2, 40)

    player_lives = 3
    ai_lives = 3
    score = 0

    global balls, last_ball_mult_time
    ball_mult_interval = 30000  # 30 seconds
    reset_level(player_paddle, ai_paddle)

    font = pygame.font.SysFont("Arial", 20)

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_paddle.move(-PADDLE_SPEED)
        if keys[pygame.K_RIGHT]:
            player_paddle.move(PADDLE_SPEED)

        ai_paddle.update(balls)

        for ball in balls:
            ball.update()

            if ball.rect.left <= 0 or ball.rect.right >= SCREEN_WIDTH:
                ball.vx = -ball.vx
                if hit_sound:
                    hit_sound.play()

            if ball.rect.top <= 0:
                ai_lives -= 1
                if lost_sound:
                    lost_sound.play()
                reset_level(player_paddle, ai_paddle)
                break
            if ball.rect.bottom >= SCREEN_HEIGHT:
                player_lives -= 1
                if lost_sound:
                    lost_sound.play()
                reset_level(player_paddle, ai_paddle)
                break

            if ball.rect.colliderect(player_paddle.rect) and ball.vy > 0:
                ball.vy = -abs(ball.vy)
                ball.vx = INITIAL_BALL_SPEED * ((ball.rect.centerx - player_paddle.rect.centerx) / (PADDLE_WIDTH / 2))
                if hit_sound:
                    hit_sound.play()

            if ball.rect.colliderect(ai_paddle.rect) and ball.vy < 0:
                ball.vy = abs(ball.vy)
                ball.vx = INITIAL_BALL_SPEED * ((ball.rect.centerx - ai_paddle.rect.centerx) / (PADDLE_WIDTH / 2))
                if hit_sound:
                    hit_sound.play()

            for brick in bricks[:]:
                if ball.rect.colliderect(brick.rect):
                    ball.vy = -ball.vy
                    if brick_sound:
                        brick_sound.play()
                    if brick.hit():
                        bricks.remove(brick)
                        score += 10
                    break

        screen.fill(BLACK)

        for brick in bricks:
            pygame.draw.rect(screen, brick.color, brick.rect)

        pygame.draw.rect(screen, WHITE, player_paddle.rect)
        pygame.draw.rect(screen, WHITE, ai_paddle.rect)

        for ball in balls:
            pygame.draw.ellipse(screen, WHITE, ball.rect)

        pygame.display.flip()

        if player_lives <= 0 or ai_lives <= 0:
            running = False

    pygame.quit()

if __name__ == "__main__":
    main()
