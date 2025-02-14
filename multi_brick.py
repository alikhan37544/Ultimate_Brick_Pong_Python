import pygame
import random
import time

# ---------------------------- DIMENSIONS ----------------------------
GAME_WIDTH = 1200
SIDE_WIDTH = 400
SCREEN_WIDTH = GAME_WIDTH + SIDE_WIDTH  # Total width (game area + side panel)
SCREEN_HEIGHT = 800
FPS = 60

# ---------------------------- PROPERTIES ----------------------------
# Paddle properties
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_SPEED = 20  # increased speed

# Ball properties
BALL_RADIUS = 10
INITIAL_BALL_SPEED = 5

# Brick properties
BRICK_ROWS = 6
BRICK_COLS = 10
BRICK_WIDTH = 70
BRICK_HEIGHT = 30
BRICK_GAP = 5

# Ball multiplication interval (milliseconds)
BALL_MULT_INTERVAL = 30000  # 30 seconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (50, 50, 50)
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
        if self.rect.right > GAME_WIDTH:
            self.rect.right = GAME_WIDTH

class AIPaddle(Paddle):
    def __init__(self, x, y):
        super().__init__(x, y)

    def update(self, balls):
        """A simple AI that tracks the closest ball horizontally."""
        if balls:
            # Choose the ball that is closest vertically to the AI paddle.
            closest_ball = min(balls, key=lambda b: abs(b.rect.centery - self.rect.centery))
            if closest_ball.rect.centerx < self.rect.centerx:
                self.move(-PADDLE_SPEED)
            elif closest_ball.rect.centerx > self.rect.centerx:
                self.move(PADDLE_SPEED)

class Ball:
    def __init__(self, x, y, vy_direction):
        # vy_direction should be -1 for a ball above the player's paddle (going upward)
        # and 1 for a ball below the AI paddle (going downward).
        self.rect = pygame.Rect(x - BALL_RADIUS, y - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)
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
            self.hits = -1  # unbreakable
            self.color = GRAY

    def hit(self):
        if self.hits > 0:
            self.hits -= 1
            if self.hits == 0:
                return True  # Brick should be removed.
            else:
                # Darken the color a little to indicate damage.
                self.color = (
                    max(self.color[0]-50, 0),
                    max(self.color[1]-50, 0),
                    max(self.color[2]-50, 0)
                )
        return False

# ---------------------------- HELPER FUNCTIONS ----------------------------
def create_bricks():
    bricks = []
    total_width = BRICK_COLS * BRICK_WIDTH + (BRICK_COLS - 1) * BRICK_GAP
    total_height = BRICK_ROWS * BRICK_HEIGHT + (BRICK_ROWS - 1) * BRICK_GAP
    offset_x = (GAME_WIDTH - total_width) // 2
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
    # Spawn one ball for the player (above the paddle, going upward)
    balls.append(Ball(player_paddle.rect.centerx, player_paddle.rect.top - 20, -1))
    # Spawn one ball for the AI (below the paddle, going downward)
    balls.append(Ball(ai_paddle.rect.centerx, ai_paddle.rect.bottom + 20, 1))
    last_ball_mult_time = pygame.time.get_ticks()
    bricks = create_bricks()

def draw_side_panel(screen, font, metrics):
    # Draw the background for the side panel.
    panel_rect = pygame.Rect(GAME_WIDTH, 0, SIDE_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, DARK_GRAY, panel_rect)

    # Draw metrics text.
    y_offset = 20
    line_spacing = 30
    for key, value in metrics.items():
        text_surface = font.render(f"{key}: {value}", True, WHITE)
        screen.blit(text_surface, (GAME_WIDTH + 20, y_offset))
        y_offset += line_spacing

# ---------------------------- MAIN GAME LOOP ----------------------------
def main():
    global balls, last_ball_mult_time

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Brick Versus - AI Metrics")
    clock = pygame.time.Clock()

    # Load sound effects (if available)
    try:
        hit_sound = pygame.mixer.Sound("hit.wav")
        brick_sound = pygame.mixer.Sound("brick.wav")
        lost_sound = pygame.mixer.Sound("lost.wav")
    except Exception as e:
        print("Sound files not found or could not be loaded; continuing without sound.")
        hit_sound = brick_sound = lost_sound = None

    # Create paddles.
    player_paddle = Paddle((GAME_WIDTH - PADDLE_WIDTH) // 2, SCREEN_HEIGHT - 60)
    ai_paddle = AIPaddle((GAME_WIDTH - PADDLE_WIDTH) // 2, 40)

    # Game metrics.
    player_lives = 3
    ai_lives = 3
    score = 0

    # Initialize balls and bricks.
    global balls
    last_ball_mult_time = pygame.time.get_ticks()
    reset_level(player_paddle, ai_paddle)

    font = pygame.font.SysFont("Arial", 20)

    running = True
    while running:
        dt = clock.tick(FPS)
        current_time = pygame.time.get_ticks()

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

        # --- Update Balls ---
        for ball in balls:
            ball.update()

            # Bounce off side walls (using GAME_WIDTH for boundaries)
            if ball.rect.left <= 0 or ball.rect.right >= GAME_WIDTH:
                ball.vx = -ball.vx
                if hit_sound:
                    hit_sound.play()

            # Check if ball goes off the top or bottom.
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

            # Collision with player paddle (only when ball is moving downward)
            if ball.rect.colliderect(player_paddle.rect) and ball.vy > 0:
                ball.vy = -abs(ball.vy)
                offset = (ball.rect.centerx - player_paddle.rect.centerx) / (PADDLE_WIDTH / 2)
                ball.vx = INITIAL_BALL_SPEED * offset
                if hit_sound:
                    hit_sound.play()

            # Collision with AI paddle (only when ball is moving upward)
            if ball.rect.colliderect(ai_paddle.rect) and ball.vy < 0:
                ball.vy = abs(ball.vy)
                offset = (ball.rect.centerx - ai_paddle.rect.centerx) / (PADDLE_WIDTH / 2)
                ball.vx = INITIAL_BALL_SPEED * offset
                if hit_sound:
                    hit_sound.play()

            # Collision with bricks.
            for brick in bricks[:]:
                if ball.rect.colliderect(brick.rect):
                    ball.vy = -ball.vy
                    if brick_sound:
                        brick_sound.play()
                    if brick.hit():
                        bricks.remove(brick)
                        score += 10
                    break

        # --- Ball Multiplication ---
        if current_time - last_ball_mult_time > BALL_MULT_INTERVAL:
            # For each current ball, spawn a new one with inverted x-velocity.
            new_balls = []
            for ball in balls:
                new_ball = Ball(ball.rect.centerx, ball.rect.centery, 1 if ball.vy > 0 else -1)
                new_ball.vx = -ball.vx
                new_ball.vy = ball.vy
                new_balls.append(new_ball)
            balls.extend(new_balls)
            last_ball_mult_time = current_time

        # --- Prepare AI Metrics for Side Panel ---
        # Determine the AI's target ball and its decision.
        if balls:
            target_ball = min(balls, key=lambda b: abs(b.rect.centery - ai_paddle.rect.centery))
            target_x = target_ball.rect.centerx
            ai_center = ai_paddle.rect.centerx
            diff = target_x - ai_center
            if diff < -5:
                decision = "Left"
            elif diff > 5:
                decision = "Right"
            else:
                decision = "Stay"
        else:
            target_x = ai_center = diff = 0
            decision = "N/A"

        time_remaining = max(0, (BALL_MULT_INTERVAL - (current_time - last_ball_mult_time)) / 1000)

        metrics = {
            "Score": score,
            "Player Lives": player_lives,
            "AI Lives": ai_lives,
            "Ball Count": len(balls),
            "Ball Mult (s)": f"{time_remaining:.1f}",
            "--- AI INFO ---": "",
            "Target Ball X": target_x,
            "AI Paddle X": ai_center,
            "Diff": diff,
            "Decision": decision
        }

        # --- DRAWING ---
        # Draw game area background.
        game_area = pygame.Rect(0, 0, GAME_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(screen, BLACK, game_area)

        # Draw bricks.
        for brick in bricks:
            pygame.draw.rect(screen, brick.color, brick.rect)

        # Draw paddles.
        pygame.draw.rect(screen, WHITE, player_paddle.rect)
        pygame.draw.rect(screen, WHITE, ai_paddle.rect)

        # Draw balls.
        for ball in balls:
            pygame.draw.ellipse(screen, WHITE, ball.rect)

        # Draw side panel with metrics.
        draw_side_panel(screen, font, metrics)

        pygame.display.flip()

        # --- GAME OVER CHECK ---
        if player_lives <= 0 or ai_lives <= 0:
            running = False

    pygame.quit()

if __name__ == "__main__":
    main()
