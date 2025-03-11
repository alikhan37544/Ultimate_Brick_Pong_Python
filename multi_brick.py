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

# Update the Ball class for better physics
class Ball:
    def __init__(self, x, y, vy_direction):
        self.rect = pygame.Rect(x - BALL_RADIUS, y - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)
        self.vx = random.choice([-1, 1]) * INITIAL_BALL_SPEED
        self.vy = vy_direction * INITIAL_BALL_SPEED
        self.trail = []  # Store previous positions for trail effect

    def update(self):
        # Store current position for trail
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 5:  # Limit trail length
            self.trail.pop(0)
            
        # Update position
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        # Keep ball within horizontal boundaries
        if self.rect.left < 0:
            self.rect.left = 0
            self.vx = abs(self.vx)  # Ensure positive x velocity
            # Add small random variation for bounces
            self.vx += random.uniform(-0.2, 0.2)
        elif self.rect.right > GAME_WIDTH:
            self.rect.right = GAME_WIDTH
            self.vx = -abs(self.vx)  # Ensure negative x velocity
            # Add small random variation for bounces
            self.vx += random.uniform(-0.2, 0.2)
            
        # Limit maximum speed
        max_speed = INITIAL_BALL_SPEED * 2.5
        if abs(self.vx) > max_speed:
            self.vx = max_speed if self.vx > 0 else -max_speed
        if abs(self.vy) > max_speed:
            self.vy = max_speed if self.vy > 0 else -max_speed

# Update the Brick class to include special types
class Brick:
    def __init__(self, x, y, brick_type):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
        self.type = brick_type
        self.velocity = [0, 0]  # For moving bricks
        
        if brick_type == 1:
            self.hits = 1
            self.color = BLUE
        elif brick_type == 2:
            self.hits = 3
            self.color = RED
        elif brick_type == 3:
            self.hits = -1  # unbreakable
            self.color = GRAY
        elif brick_type == 4:  # Boss brick
            self.hits = 10  # Will be overridden
            self.color = (255, 215, 0)  # Gold
        elif brick_type == 5:  # Moving brick
            self.hits = 2
            self.color = (0, 255, 128)  # Teal
            self.velocity = [random.choice([-1, 1]) * 2, 0]  # Horizontal movement

    def update(self):
        # For moving bricks
        if self.type == 5:
            self.rect.x += self.velocity[0]
            # Bounce off walls
            if self.rect.left <= 0:
                self.velocity[0] = abs(self.velocity[0])  # Ensure positive velocity
                self.rect.left = 0  # Explicitly position at left boundary
            elif self.rect.right >= GAME_WIDTH:
                self.velocity[0] = -abs(self.velocity[0])  # Ensure negative velocity
                self.rect.right = GAME_WIDTH  # Explicitly position at right boundary

    def hit(self):
        if self.hits > 0:
            self.hits -= 1
            if self.hits == 0:
                return True  # Brick should be removed.
            else:
                # Darken the color a little to indicate damage.
                self.color = (
                    max(self.color[0]-30, 0),
                    max(self.color[1]-30, 0),
                    max(self.color[2]-30, 0)
                )
                # Boss bricks change color more dramatically
                if self.type == 4:
                    self.color = (
                        255,  # Keep red high
                        max(self.color[1]-50, 0),  # Reduce green
                        min(self.color[2]+50, 255)  # Increase blue
                    )
        return False

# Update the PowerUp class
class PowerUp:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 15, y - 15, 30, 30)
        self.type = random.choice(["speed", "size", "multi", "life", "laser", "slow"])  # Added new types
        self.vy = 2  # Falling speed
        self.pulse = 0  # For pulsing effect
        self.pulse_dir = 1
        
        # Determine color based on type
        if self.type == "speed":
            self.color = (255, 255, 0)  # Yellow
        elif self.type == "size":
            self.color = (0, 255, 0)    # Green
        elif self.type == "multi":
            self.color = (255, 0, 255)  # Purple
        elif self.type == "life":
            self.color = (255, 128, 0)  # Orange
        elif self.type == "laser":
            self.color = (50, 150, 255) # Light blue
        elif self.type == "slow":
            self.color = (0, 200, 200)  # Teal
            
    def update(self):
        self.rect.y += self.vy
        # Pulsing effect
        self.pulse += 0.1 * self.pulse_dir
        if self.pulse >= 1.0 or self.pulse <= 0.0:
            self.pulse_dir *= -1
        
    def apply(self, player_paddle, ai_paddle, balls):
        if self.type == "speed":
            # Increase ball speed
            for ball in balls:
                ball.vx *= 1.1
                ball.vy *= 1.1
        elif self.type == "size":
            # Increase paddle size
            player_paddle.rect.width = min(PADDLE_WIDTH * 2, player_paddle.rect.width * 1.2)
        elif self.type == "multi":
            # Add a new ball
            if balls:
                new_ball = Ball(balls[0].rect.centerx, balls[0].rect.centery, 
                              -1 if balls[0].vy > 0 else 1)
                balls.append(new_ball)
        elif self.type == "life":
            # Add a life
            return 1
        elif self.type == "laser":
            # Add laser effect
            effects.append({
                "type": "laser", 
                "x": player_paddle.rect.centerx, 
                "y": player_paddle.rect.top,
                "width": 5,
                "height": player_paddle.rect.top,
                "life": 60,
                "color": (50, 150, 255)
            })
        elif self.type == "slow":
            # Slow down balls temporarily
            for ball in balls:
                ball.vx *= 0.7
                ball.vy *= 0.7
        return 0

# ---------------------------- HELPER FUNCTIONS ----------------------------
# Update the create_bricks function for more interesting layouts:

def create_bricks(level=1):
    bricks = []
    total_width = BRICK_COLS * BRICK_WIDTH + (BRICK_COLS - 1) * BRICK_GAP
    total_height = BRICK_ROWS * BRICK_HEIGHT + (BRICK_ROWS - 1) * BRICK_GAP
    offset_x = (GAME_WIDTH - total_width) // 2
    offset_y = 100  # Fixed offset from top for consistency
    
    # Different patterns based on level
    layout_type = level % 5  # 5 different layouts

    if layout_type == 0:  # Standard pattern
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                if random.random() < 0.85:  # Higher chance to create a brick
                    x = offset_x + col * (BRICK_WIDTH + BRICK_GAP)
                    y = offset_y + row * (BRICK_HEIGHT + BRICK_GAP)
                    # Higher levels = more tough bricks
                    weights = [max(50 - level * 5, 10), 30 + level * 2, 20 + level]
                    brick_type = random.choices([1, 2, 3], weights=weights)[0]
                    bricks.append(Brick(x, y, brick_type))
    
    elif layout_type == 1:  # Checkerboard pattern
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                if (row + col) % 2 == 0:
                    x = offset_x + col * (BRICK_WIDTH + BRICK_GAP)
                    y = offset_y + row * (BRICK_HEIGHT + BRICK_GAP)
                    brick_type = random.choices([1, 2, 3], weights=[40, 40, 20])[0]
                    bricks.append(Brick(x, y, brick_type))
    
    elif layout_type == 2:  # Fortress pattern with more unbreakable bricks
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                if row == 0 or row == BRICK_ROWS-1 or col == 0 or col == BRICK_COLS-1:
                    # Create border of tough bricks
                    x = offset_x + col * (BRICK_WIDTH + BRICK_GAP)
                    y = offset_y + row * (BRICK_HEIGHT + BRICK_GAP)
                    brick_type = random.choices([2, 3], weights=[30, 70])[0]
                    bricks.append(Brick(x, y, brick_type))
                elif random.random() < 0.6:  # Interior bricks
                    x = offset_x + col * (BRICK_WIDTH + BRICK_GAP)
                    y = offset_y + row * (BRICK_HEIGHT + BRICK_GAP)
                    brick_type = random.choices([1, 2], weights=[70, 30])[0]
                    bricks.append(Brick(x, y, brick_type))
    
    elif layout_type == 3:  # Triangle pattern
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                if col >= (BRICK_COLS - row - 1) // 2 and col < (BRICK_COLS + row + 1) // 2:
                    x = offset_x + col * (BRICK_WIDTH + BRICK_GAP)
                    y = offset_y + row * (BRICK_HEIGHT + BRICK_GAP)
                    brick_type = random.choices([1, 2, 3], weights=[50, 30, 20])[0]
                    bricks.append(Brick(x, y, brick_type))
    
    else:  # Circular pattern
        center_col = BRICK_COLS // 2
        center_row = BRICK_ROWS // 2
        max_radius = min(BRICK_COLS, BRICK_ROWS) // 2
        
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                # Calculate distance from center
                dx = col - center_col
                dy = row - center_row
                distance = ((dx ** 2) + (dy ** 2)) ** 0.5
                
                if distance <= max_radius:
                    x = offset_x + col * (BRICK_WIDTH + BRICK_GAP)
                    y = offset_y + row * (BRICK_HEIGHT + BRICK_GAP)
                    # Bricks get tougher toward center
                    if distance <= max_radius / 3:  # Inner circle
                        brick_type = 3
                    elif distance <= max_radius * 2/3:  # Middle circle
                        brick_type = 2
                    else:  # Outer circle
                        brick_type = 1
                    bricks.append(Brick(x, y, brick_type))
                    
    # Add special "boss" brick for higher levels
    if level > 3 and level % 3 == 0:
        x = offset_x + (BRICK_COLS // 2) * (BRICK_WIDTH + BRICK_GAP)
        y = offset_y + (BRICK_ROWS // 2) * (BRICK_HEIGHT + BRICK_GAP)
        boss_brick = Brick(x, y, 4)  # New brick type 4 for boss brick
        boss_brick.hits = level * 2  # More hits based on level
        boss_brick.color = (255, 215, 0)  # Gold color
        boss_brick.rect.width *= 2  # Double width
        bricks.append(boss_brick)
                    
    return bricks

def reset_level(player_paddle, ai_paddle, level=1):
    global balls, bricks, last_ball_mult_time, power_ups, effects
    
    # Clear any existing power-ups and effects
    power_ups = []
    effects = []
    
    # Reset balls
    balls = []
    # Spawn one ball for the player (above the paddle, going upward)
    balls.append(Ball(player_paddle.rect.centerx, player_paddle.rect.top - 20, -1))
    # Spawn one ball for the AI (below the paddle, going downward)
    balls.append(Ball(ai_paddle.rect.centerx, ai_paddle.rect.bottom + 20, 1))
    
    last_ball_mult_time = pygame.time.get_ticks()
    
    # Create bricks with level-specific patterns
    bricks = create_bricks(level)

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
    global balls, last_ball_mult_time, bricks

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Brick Versus - Enhanced Edition")
    clock = pygame.time.Clock()

    # Load sound effects (if available)
    try:
        hit_sound = pygame.mixer.Sound("hit.wav")
        brick_sound = pygame.mixer.Sound("brick.wav")
        lost_sound = pygame.mixer.Sound("lost.wav")
        powerup_sound = pygame.mixer.Sound("powerup.wav")
    except Exception as e:
        print("Sound files not found or could not be loaded; continuing without sound.")
        hit_sound = brick_sound = lost_sound = powerup_sound = None

    # Create paddles
    player_paddle = Paddle((GAME_WIDTH - PADDLE_WIDTH) // 2, SCREEN_HEIGHT - 60)
    ai_paddle = AIPaddle((GAME_WIDTH - PADDLE_WIDTH) // 2, 40)

    # Game metrics
    player_lives = 3
    ai_lives = 3
    score = 0
    power_ups = []
    effects = []  # Visual effects
    game_state = "playing"  # Can be "playing", "paused", "game_over"
    level = 1

    # Initialize balls and bricks
    global balls
    last_ball_mult_time = pygame.time.get_ticks()
    reset_level(player_paddle, ai_paddle, level)

    font = pygame.font.SysFont("Arial", 20)
    large_font = pygame.font.SysFont("Arial", 40)

    running = True
    while running:
        dt = clock.tick(FPS)
        current_time = pygame.time.get_ticks()

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    game_state = "paused" if game_state == "playing" else "playing"
                if event.key == pygame.K_r and game_state == "game_over":
                    player_lives = 3
                    ai_lives = 3
                    score = 0
                    level = 1
                    reset_level(player_paddle, ai_paddle, level)
                    game_state = "playing"

        if game_state != "playing":
            # Draw pause/game over screen
            if game_state == "paused":
                pause_text = large_font.render("PAUSED", True, WHITE)
                screen.blit(pause_text, (GAME_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2))
            elif game_state == "game_over":
                result = "YOU WIN!" if ai_lives <= 0 else "GAME OVER"
                game_over_text = large_font.render(result, True, WHITE)
                restart_text = font.render("Press R to restart", True, WHITE)
                screen.blit(game_over_text, (GAME_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
                screen.blit(restart_text, (GAME_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
            
            pygame.display.flip()
            continue

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

            # Check if ball goes off the top or bottom
            if ball.rect.top <= 0:
                ai_lives -= 1
                if lost_sound:
                    lost_sound.play()
                # Create explosion effect
                effects.append({"type": "explosion", "x": ball.rect.centerx, "y": ball.rect.centery, 
                              "radius": 10, "max_radius": 40, "color": RED})
                balls.remove(ball)
                if len(balls) == 0:
                    reset_level(player_paddle, ai_paddle)
                    if ai_lives <= 0:
                        game_state = "game_over"
                continue
                
            if ball.rect.bottom >= SCREEN_HEIGHT:
                player_lives -= 1
                if lost_sound:
                    lost_sound.play()
                # Create explosion effect
                effects.append({"type": "explosion", "x": ball.rect.centerx, "y": ball.rect.centery, 
                              "radius": 10, "max_radius": 40, "color": BLUE})
                balls.remove(ball)
                if len(balls) == 0:
                    reset_level(player_paddle, ai_paddle)
                    if player_lives <= 0:
                        game_state = "game_over"
                continue

            # Collision with player paddle (only when ball is moving downward)
            if ball.rect.colliderect(player_paddle.rect) and ball.vy > 0:
                ball.vy = -abs(ball.vy)
                # Calculate angle based on where the ball hit the paddle
                offset = (ball.rect.centerx - player_paddle.rect.centerx) / (player_paddle.rect.width / 2)
                ball.vx = INITIAL_BALL_SPEED * offset * 1.5
                # Reposition ball above paddle
                ball.rect.bottom = player_paddle.rect.top
                if hit_sound:
                    hit_sound.play()

            # Collision with AI paddle (only when ball is moving upward)
            if ball.rect.colliderect(ai_paddle.rect) and ball.vy < 0:
                ball.vy = abs(ball.vy)
                offset = (ball.rect.centerx - ai_paddle.rect.centerx) / (ai_paddle.rect.width / 2)
                ball.vx = INITIAL_BALL_SPEED * offset * 1.5
                # Reposition ball below paddle
                ball.rect.top = ai_paddle.rect.bottom
                if hit_sound:
                    hit_sound.play()

            # Collision with bricks
            for brick in bricks[:]:
                if ball.rect.colliderect(brick.rect):
                    # Calculate previous position to determine collision direction
                    prev_x = ball.rect.x - ball.vx
                    prev_y = ball.rect.y - ball.vy
                    prev_rect = pygame.Rect(prev_x, prev_y, ball.rect.width, ball.rect.height)
                    
                    # Horizontal collision
                    if (prev_rect.right <= brick.rect.left or prev_rect.left >= brick.rect.right):
                        ball.vx = -ball.vx
                        # Position adjustment to prevent sticking
                        if ball.rect.centerx < brick.rect.centerx:
                            ball.rect.right = brick.rect.left - 1
                        else:
                            ball.rect.left = brick.rect.right + 1
                    # Vertical collision
                    else:
                        ball.vy = -ball.vy
                        # Position adjustment to prevent sticking
                        if ball.rect.centery < brick.rect.centery:
                            ball.rect.bottom = brick.rect.top - 1
                        else:
                            ball.rect.top = brick.rect.bottom + 1
                    
                    if brick_sound:
                        brick_sound.play()
                        
                    if brick.hit():
                        bricks.remove(brick)
                        score += 10 * level
                        # Create enhanced particle effect
                        for _ in range(15):  # More particles
                            effects.append({
                                "type": "particle",
                                "x": brick.rect.centerx,
                                "y": brick.rect.centery,
                                "vx": random.uniform(-4, 4),
                                "vy": random.uniform(-4, 4),
                                "life": 40,
                                "size": random.randint(2, 6),  # Variable sizes
                                "color": brick.color
                            })
                        # Chance to spawn power-up
                        if random.random() < 0.25:  # Slightly higher chance
                            power_ups.append(PowerUp(brick.rect.centerx, brick.rect.centery))
                    break

        # Add this to the main game loop, before drawing:

        # --- Update Moving Bricks ---
        for brick in bricks:
            if hasattr(brick, 'update'):
                brick.update()

        # --- Update Power-ups ---
        for power_up in power_ups[:]:
            power_up.update()
            
            # Check if power-up is collected by player
            if power_up.rect.colliderect(player_paddle.rect):
                extra_life = power_up.apply(player_paddle, ai_paddle, balls)
                player_lives += extra_life
                power_ups.remove(power_up)
                if powerup_sound:
                    powerup_sound.play()
                continue
                
            # Remove if off-screen
            if power_up.rect.top > SCREEN_HEIGHT:
                power_ups.remove(power_up)

        # --- Update visual effects ---
        for effect in effects[:]:
            if effect["type"] == "explosion":
                effect["radius"] += 2
                if effect["radius"] >= effect["max_radius"]:
                    effects.remove(effect)
            elif effect["type"] == "particle":
                effect["x"] += effect["vx"]
                effect["y"] += effect["vy"]
                effect["life"] -= 1
                if effect["life"] <= 0:
                    effects.remove(effect)

        # --- Check Level Completion ---
        if len(bricks) == 0:
            level += 1
            reset_level(player_paddle, ai_paddle)
            # Reset paddle size for new level
            player_paddle.rect.width = PADDLE_WIDTH
            ai_paddle.rect.width = PADDLE_WIDTH

        # --- Ball Multiplication ---
        if current_time - last_ball_mult_time > BALL_MULT_INTERVAL and len(balls) < 6:  # Limit max balls
            # For each current ball, spawn a new one with inverted x-velocity
            new_balls = []
            for ball in balls:
                new_ball = Ball(ball.rect.centerx, ball.rect.centery, 1 if ball.vy > 0 else -1)
                new_ball.vx = -ball.vx
                new_ball.vy = ball.vy
                new_balls.append(new_ball)
            balls.extend(new_balls)
            last_ball_mult_time = current_time

        # --- Prepare AI Metrics for Side Panel ---
        # Determine the AI's target ball and its decision
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
            "Level": level,
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
        # Draw game area background with gradient
        for y in range(0, SCREEN_HEIGHT, 4):
            color_value = 20 + (y / SCREEN_HEIGHT * 30)
            pygame.draw.rect(screen, (0, 0, color_value), pygame.Rect(0, y, GAME_WIDTH, 4))

        # Draw bricks with 3D effect
        for brick in bricks:
            # Main brick body
            pygame.draw.rect(screen, brick.color, brick.rect)
            
            # 3D effect - top and left edges (lighter)
            light_color = tuple(min(c + 40, 255) for c in brick.color)
            pygame.draw.line(screen, light_color, brick.rect.topleft, brick.rect.topright)
            pygame.draw.line(screen, light_color, brick.rect.topleft, brick.rect.bottomleft)
            
            # 3D effect - bottom and right edges (darker)
            dark_color = tuple(max(c - 40, 0) for c in brick.color)
            pygame.draw.line(screen, dark_color, brick.rect.bottomleft, brick.rect.bottomright)
            pygame.draw.line(screen, dark_color, brick.rect.topright, brick.rect.bottomright)

        # Draw improved visual effects
        for effect in effects:
            if effect["type"] == "explosion":
                # Draw multiple circles for explosion effect
                for radius in range(effect["radius"], max(0, effect["radius"] - 15), -3):
                    alpha = (radius / effect["max_radius"]) * 255
                    color = (effect["color"][0], effect["color"][1], effect["color"][2], alpha)
                    pygame.draw.circle(screen, color, (effect["x"], effect["y"]), radius, 2)
            elif effect["type"] == "particle":
                # Draw particles with fadeout
                alpha = effect["life"] * 8  # Fade out based on life
                color = effect["color"]
                size = effect.get("size", 4)
                pygame.draw.rect(screen, color, pygame.Rect(effect["x"], effect["y"], size, size))
            elif effect["type"] == "laser":
                # Draw laser effect
                pygame.draw.rect(screen, effect["color"], 
                                pygame.Rect(effect["x"] - effect["width"]//2, 0, effect["width"], effect["y"]))
                # Add glow effect
                for w in range(1, 10, 2):
                    glow_color = (effect["color"][0], effect["color"][1], effect["color"][2], 150 - w*15)
                    pygame.draw.rect(screen, glow_color, 
                                   pygame.Rect(effect["x"] - (effect["width"] + w)//2, 0, effect["width"] + w, effect["y"]))

        # Draw power-ups with glowing effect
        for power_up in power_ups:
            # Main power-up
            pygame.draw.ellipse(screen, power_up.color, power_up.rect)
            
            # Pulsing glow
            glow_size = int(8 * power_up.pulse)
            glow_rect = pygame.Rect(
                power_up.rect.x - glow_size,
                power_up.rect.y - glow_size,
                power_up.rect.width + glow_size*2,
                power_up.rect.height + glow_size*2
            )
            # Adjust alpha based on pulse
            glow_alpha = int(128 * power_up.pulse)
            # FIX: Remove alpha component - pygame.draw.ellipse doesn't support RGBA
            glow_color = (power_up.color[0], power_up.color[1], power_up.color[2])
            pygame.draw.ellipse(screen, glow_color, glow_rect, 2)
            
        # Draw paddles with glow effect
        pygame.draw.rect(screen, WHITE, player_paddle.rect)
        pygame.draw.rect(screen, (200, 200, 255), pygame.Rect(
            player_paddle.rect.x - 2,
            player_paddle.rect.y - 2,
            player_paddle.rect.width + 4,
            player_paddle.rect.height + 4
        ), 2)  # Player paddle glow

        pygame.draw.rect(screen, WHITE, ai_paddle.rect)
        pygame.draw.rect(screen, (255, 200, 200), pygame.Rect(
            ai_paddle.rect.x - 2,
            ai_paddle.rect.y - 2,
            ai_paddle.rect.width + 4,
            ai_paddle.rect.height + 4
        ), 2)  # AI paddle glow

        # Draw balls with trail effect
        for ball in balls:
            # Add trail effect
            for i in range(1, 4):
                trail_pos = (
                    ball.rect.centerx - ball.vx * i*1.5,
                    ball.rect.centery - ball.vy * i*1.5
                )
                trail_radius = BALL_RADIUS - i*2
                if trail_radius > 0:
                    alpha = 255 - i*60
                    trail_color = (255, 255, 255, alpha)
                    pygame.draw.circle(screen, trail_color, trail_pos, trail_radius)
            
            # Draw the main ball
            pygame.draw.ellipse(screen, WHITE, ball.rect)
            # Ball glow
            glow_rect = pygame.Rect(
                ball.rect.x - 3,
                ball.rect.y - 3,
                ball.rect.width + 6,
                ball.rect.height + 6
            )
            pygame.draw.ellipse(screen, (200, 200, 255, 100), glow_rect, 2)

        # Draw side panel with metrics
        draw_side_panel(screen, font, metrics)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
