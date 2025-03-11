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
BRICK_ROWS = 10  # Increased from 6
BRICK_COLS = 14  # Increased from 10
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

# Add these global variables near the top with the other globals
player_brick_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}  # Track bricks broken by player
ai_brick_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}      # Track bricks broken by AI
player_balls_lost = 0  # Track balls lost by player
ai_balls_lost = 0      # Track balls lost by AI
player_round_score = 0 # Player's score for current round
ai_round_score = 0     # AI's score for current round
player_total_score = 0 # Player's total score across rounds
ai_total_score = 0     # AI's total score across rounds
round_number = 1       # Current round number
round_winner = ""      # Winner of the current round
showing_round_summary = False # Flag to control round summary display
round_summary_start_time = 0  # When the round summary started

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
        self.last_hit_by = "player" if vy_direction < 0 else "ai"  # Track who last hit the ball

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
    def __init__(self, x, y, direction="down"):
        self.rect = pygame.Rect(x - 15, y - 15, 30, 30)
        # Update powerup types: replaced "life" with "score"
        self.type = random.choice(["speed", "size", "multi", "score", "laser", "slow"])
        self.vy = 2 if direction == "down" else -2  # Direction of movement
        self.direction = direction  # "down" (toward player) or "up" (toward AI)
        self.pulse = 0  # For pulsing effect
        self.pulse_dir = 1
        
        # Determine color based on type
        if self.type == "speed":
            self.color = (255, 255, 0)  # Yellow
        elif self.type == "size":
            self.color = (0, 255, 0)    # Green
        elif self.type == "multi":
            self.color = (255, 0, 255)  # Purple
        elif self.type == "score":      # Changed from "life" to "score", new color
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
        
    def apply(self, player_paddle, ai_paddle, balls, collector="player"):
        # Initialize extra lives and scores
        extra_player_lives = 0
        extra_ai_lives = 0
        score_bonus = 0
        
        # Create notification text
        notification_text = f"{collector.upper()} got {self.type.upper()}!"
        notification_color = BLUE if collector == "player" else RED
        
        # Add text effect notification
        effects.append({
            "type": "text",
            "text": notification_text,
            "x": GAME_WIDTH // 2,
            "y": SCREEN_HEIGHT // 2,
            "life": 120,
            "color": notification_color
        })
        
        if self.type == "speed":
            # Increase ball speed
            for ball in balls:
                ball.vx *= 1.1
                ball.vy *= 1.1
        elif self.type == "size":
            # Increase paddle size of the collector only
            if collector == "player":
                player_paddle.rect.width = min(PADDLE_WIDTH * 2, player_paddle.rect.width * 1.2)
            else:
                ai_paddle.rect.width = min(PADDLE_WIDTH * 2, ai_paddle.rect.width * 1.2)
        elif self.type == "multi":
            # Add a new ball
            if balls:
                new_ball = Ball(balls[0].rect.centerx, balls[0].rect.centery, 
                              -1 if collector == "player" else 1)
                new_ball.last_hit_by = collector
                balls.append(new_ball)
        elif self.type == "score":
            # Add score bonus (replaces life powerup)
            score_bonus = 20  # 20 points bonus
            effects.append({
                "type": "text",
                "text": "+20 POINTS!",
                "x": GAME_WIDTH // 2,
                "y": SCREEN_HEIGHT // 2 + 40,
                "life": 120,
                "color": notification_color
            })
        elif self.type == "laser":
            # Enhanced laser effect that destroys bricks in its path
            laser_x = player_paddle.rect.centerx if collector == "player" else ai_paddle.rect.centerx
            laser_y_start = player_paddle.rect.top if collector == "player" else ai_paddle.rect.bottom
            laser_color = (50, 150, 255) if collector == "player" else (255, 50, 50)
            
            # Add visual laser effect
            effects.append({
                "type": "laser", 
                "x": laser_x, 
                "y": laser_y_start if collector == "player" else SCREEN_HEIGHT - laser_y_start,
                "width": 5,
                "height": SCREEN_HEIGHT if collector == "player" else laser_y_start,
                "life": 60,
                "color": laser_color
            })
            
            # Destroy bricks in the laser's path
            laser_width = 20  # Width of the effective laser beam
            bricks_destroyed = 0
            
            # Check for brick collisions with the laser beam
            for brick in bricks[:]:
                # If the laser passes through this brick
                if abs(brick.rect.centerx - laser_x) < laser_width + brick.rect.width // 2:
                    # Update brick stats based on collector
                    if collector == "player":
                        player_brick_stats[brick.type] = player_brick_stats.get(brick.type, 0) + 1
                    else:
                        ai_brick_stats[brick.type] = ai_brick_stats.get(brick.type, 0) + 1
                    
                    # Create destruction effect
                    for _ in range(15):
                        effects.append({
                            "type": "particle",
                            "x": brick.rect.centerx,
                            "y": brick.rect.centery,
                            "vx": random.uniform(-4, 4),
                            "vy": random.uniform(-4, 4),
                            "life": 40,
                            "size": random.randint(2, 6),
                            "color": brick.color
                        })
                    
                    # Remove the brick
                    bricks.remove(brick)
                    bricks_destroyed += 1
            
            # Show how many bricks were destroyed
            if bricks_destroyed > 0:
                effects.append({
                    "type": "text",
                    "text": f"{bricks_destroyed} BRICKS DESTROYED!",
                    "x": GAME_WIDTH // 2,
                    "y": SCREEN_HEIGHT // 2 + 40,
                    "life": 120,
                    "color": notification_color
                })
                
        elif self.type == "slow":
            # Slow down balls temporarily
            for ball in balls:
                ball.vx *= 0.7
                ball.vy *= 0.7
                
        return extra_player_lives, extra_ai_lives, score_bonus

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
                    
                    # Make sure outer edge bricks are always breakable
                    if row == 0 or row == BRICK_ROWS-1 or col == 0 or col == BRICK_COLS-1:
                        brick_type = random.choices([1, 2], weights=[70, 30])[0]  # Only breakable types
                    else:
                        # Inner bricks can sometimes be unbreakable, but with reduced chance
                        brick_type = random.choices([1, 2, 3], weights=[50, 40, 10])[0]
                        
                    bricks.append(Brick(x, y, brick_type))
    
    elif layout_type == 2:  # Fortress pattern with more unbreakable bricks
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                if row == 0 or row == BRICK_ROWS-1 or col == 0 or col == BRICK_COLS-1:
                    # Create border of tough but always breakable bricks
                    x = offset_x + col * (BRICK_WIDTH + BRICK_GAP)
                    y = offset_y + row * (BRICK_HEIGHT + BRICK_GAP)
                    # Make sure there's at least one breakable brick on each side
                    if (row == 0 and col == BRICK_COLS//2) or \
                       (row == BRICK_ROWS-1 and col == BRICK_COLS//2) or \
                       (col == 0 and row == BRICK_ROWS//2) or \
                       (col == BRICK_COLS-1 and row == BRICK_ROWS//2):
                        brick_type = 1  # Always easy breakable brick as entry point
                    else:
                        # Other border bricks - still mostly breakable
                        brick_type = random.choices([1, 2, 3], weights=[20, 60, 20])[0]
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
    global breakable_brick_count, level_reset_timer, level_reset_active
    global player_brick_stats, ai_brick_stats, player_balls_lost, ai_balls_lost
    global player_round_score, ai_round_score, round_number, round_winner
    global showing_round_summary, round_summary_start_time
    
    # Reset stats for new round
    player_brick_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    ai_brick_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    player_balls_lost = 0
    ai_balls_lost = 0
    player_round_score = 0
    ai_round_score = 0
    round_winner = ""
    showing_round_summary = False
    
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
    
    # Count breakable bricks (bricks with hits > 0)
    breakable_brick_count = sum(1 for brick in bricks if brick.hits > 0)
    
    # Reset level timer
    level_reset_timer = 0
    level_reset_active = False

def draw_side_panel(screen, font, metrics):
    # Draw the background for the side panel
    panel_rect = pygame.Rect(GAME_WIDTH, 0, SIDE_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, DARK_GRAY, panel_rect)

    # Draw a cleaner, more organized side panel with sections
    y_offset = 20
    
    # --------- SECTION 1: GAME INFO ---------
    pygame.draw.rect(screen, (40, 40, 40), pygame.Rect(GAME_WIDTH + 10, y_offset - 10, SIDE_WIDTH - 20, 100))
    
    # Only show key metrics
    important_metrics = ["Score", "Level", "Ball Count", "Ball Mult (s)"]
    for key in important_metrics:
        if key in metrics:
            text_surface = font.render(f"{key}: {metrics[key]}", True, WHITE)
            screen.blit(text_surface, (GAME_WIDTH + 20, y_offset))
            y_offset += 25
    
    y_offset += 15
    
    # --------- SECTION 2: PLAYER STATS ---------
    section_bg = pygame.Rect(GAME_WIDTH + 10, y_offset - 10, SIDE_WIDTH - 20, 110)
    pygame.draw.rect(screen, (20, 20, 60), section_bg)
    pygame.draw.rect(screen, BLUE, section_bg, 2)  # Blue border
    
    # Player stats header
    screen.blit(font.render("PLAYER STATS", True, BLUE), (GAME_WIDTH + 20, y_offset))
    y_offset += 30
    
    # Current score calculation
    player_score_from_bricks = (player_brick_stats.get(1, 0) * 1 + 
                              player_brick_stats.get(2, 0) * 3 + 
                              player_brick_stats.get(3, 0) * 5 +
                              player_brick_stats.get(4, 0) * 10 +
                              player_brick_stats.get(5, 0) * 3)
    
    player_ball_penalty = min(15, sum(max(0, 6-i) for i in range(1, player_balls_lost+1)))
    current_player_score = max(0, player_score_from_bricks - player_ball_penalty)
    
    # Total bricks broken
    total_player_bricks = sum(player_brick_stats.values())
    screen.blit(font.render(f"Bricks: {total_player_bricks}  Balls lost: {player_balls_lost}", 
              True, WHITE), (GAME_WIDTH + 20, y_offset))
    y_offset += 25
    
    # Score info
    screen.blit(font.render(f"Current score: {current_player_score}", True, WHITE), 
              (GAME_WIDTH + 20, y_offset))
    y_offset += 25
    
    screen.blit(font.render(f"Total score: {player_total_score}", True, WHITE), 
              (GAME_WIDTH + 20, y_offset))
    y_offset += 40
    
    # --------- SECTION 3: AI STATS ---------
    section_bg = pygame.Rect(GAME_WIDTH + 10, y_offset - 10, SIDE_WIDTH - 20, 110)
    pygame.draw.rect(screen, (60, 20, 20), section_bg)
    pygame.draw.rect(screen, RED, section_bg, 2)  # Red border
    
    # AI stats header
    screen.blit(font.render("AI STATS", True, RED), (GAME_WIDTH + 20, y_offset))
    y_offset += 30
    
    # Current AI score calculation  
    ai_score_from_bricks = (ai_brick_stats.get(1, 0) * 1 + 
                          ai_brick_stats.get(2, 0) * 3 + 
                          ai_brick_stats.get(3, 0) * 5 +
                          ai_brick_stats.get(4, 0) * 10 +
                          ai_brick_stats.get(5, 0) * 3)
    
    ai_ball_penalty = min(15, sum(max(0, 6-i) for i in range(1, ai_balls_lost+1)))
    current_ai_score = max(0, ai_score_from_bricks - ai_ball_penalty)
    
    # Total bricks broken
    total_ai_bricks = sum(ai_brick_stats.values())
    screen.blit(font.render(f"Bricks: {total_ai_bricks}  Balls lost: {ai_balls_lost}", 
              True, WHITE), (GAME_WIDTH + 20, y_offset))
    y_offset += 25
    
    # Score info
    screen.blit(font.render(f"Current score: {current_ai_score}", True, WHITE), 
              (GAME_WIDTH + 20, y_offset))
    y_offset += 25
    
    screen.blit(font.render(f"Total score: {ai_total_score}", True, WHITE), 
              (GAME_WIDTH + 20, y_offset))
    y_offset += 40
    
    # --------- SECTION 4: ROUND INFO ---------
    section_bg = pygame.Rect(GAME_WIDTH + 10, y_offset - 10, SIDE_WIDTH - 20, 50)
    pygame.draw.rect(screen, (40, 40, 40), section_bg)
    
    screen.blit(font.render(f"ROUND: {round_number}", True, WHITE), 
              (GAME_WIDTH + 20, y_offset))
    y_offset += 25
    
    # Show who's currently winning
    if current_player_score > current_ai_score:
        leader_text = "PLAYER LEADING"
        leader_color = BLUE
    elif current_ai_score > current_player_score:
        leader_text = "AI LEADING"
        leader_color = RED
    else:
        leader_text = "TIED GAME"
        leader_color = WHITE
        
    screen.blit(font.render(leader_text, True, leader_color), 
              (GAME_WIDTH + 20, y_offset))
    y_offset += 40
    
    # --------- SECTION 5: POWER-UP LEGEND ---------
    draw_powerup_legend(screen, font, y_offset)

def show_round_summary(screen, font, large_font):
    global showing_round_summary, round_summary_start_time
    global player_brick_stats, ai_brick_stats, player_balls_lost, ai_balls_lost
    global player_round_score, ai_round_score, player_total_score, ai_total_score
    global round_winner, round_number, effects
    
    # Start the summary display
    showing_round_summary = True
    round_summary_start_time = pygame.time.get_ticks()
    
    # Clear any existing effects to prevent overlap
    effects = []
    
    # ----------- CALCULATE SCORES -----------
    player_score_from_bricks = (player_brick_stats.get(1, 0) * 1 + 
                               player_brick_stats.get(2, 0) * 3 + 
                               player_brick_stats.get(3, 0) * 5 +
                               player_brick_stats.get(4, 0) * 10 +
                               player_brick_stats.get(5, 0) * 3)
    
    ai_score_from_bricks = (ai_brick_stats.get(1, 0) * 1 + 
                           ai_brick_stats.get(2, 0) * 3 + 
                           ai_brick_stats.get(3, 0) * 5 +
                           ai_brick_stats.get(4, 0) * 10 +
                           ai_brick_stats.get(5, 0) * 3)
    
    # Calculate ball loss penalties (5 for first, 4 for second, etc)
    player_ball_penalty = min(15, sum(max(0, 6-i) for i in range(1, player_balls_lost+1)))
    ai_ball_penalty = min(15, sum(max(0, 6-i) for i in range(1, ai_balls_lost+1)))
    
    # Final round scores
    player_round_score = max(0, player_score_from_bricks - player_ball_penalty)
    ai_round_score = max(0, ai_score_from_bricks - ai_ball_penalty)
    
    # Update total scores
    player_total_score += player_round_score
    ai_total_score += ai_round_score
    
    # Determine round winner
    if player_round_score > ai_round_score:
        round_winner = "PLAYER"
        winner_color = BLUE
    elif ai_round_score > player_round_score:
        round_winner = "AI"
        winner_color = RED
    else:
        round_winner = "TIE"
        winner_color = WHITE
    
    # ----------- SIMPLIFIED ANIMATION -----------
    # Take screenshot of current game state
    game_screenshot = screen.copy()
    
    # Simple fade to black
    for alpha in range(0, 256, 32):  # Faster fade
        temp_surface = game_screenshot.copy()
        overlay = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(alpha)
        temp_surface.blit(overlay, (0, 0))
        
        if alpha > 100:  # Show text once it's dark enough
            text = large_font.render("Round Complete!", True, WHITE)
            text_rect = text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2))
            temp_surface.blit(text, text_rect)
        
        screen.blit(temp_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(20)  # Short delay
    
    pygame.time.delay(500)  # Pause at black screen
    
    # The detailed summary screen will now be drawn continuously in the main game loop
    # while showing_round_summary is True

# Add this function to draw the power-up legend:

def draw_powerup_legend(screen, font, start_y=400):
    # Draw the legend in the side panel with a background
    legend_y = start_y
    
    # Add a background for the legend
    legend_bg = pygame.Rect(GAME_WIDTH + 10, legend_y - 10, SIDE_WIDTH - 20, 180)
    pygame.draw.rect(screen, (30, 30, 40), legend_bg)
    pygame.draw.rect(screen, (100, 100, 100), legend_bg, 1)  # Gray border
    
    # Title
    screen.blit(font.render("POWER-UPS:", True, WHITE), (GAME_WIDTH + 20, legend_y))
    legend_y += 30
    
    # Simplified legend with smaller icons and more compact layout
    powerups = [
        {"name": "Speed", "desc": "Increases ball speed", "color": (255, 255, 0)},
        {"name": "Size", "desc": "Increases paddle size", "color": (0, 255, 0)},
        {"name": "Multi", "desc": "Adds an extra ball", "color": (255, 0, 255)},
        {"name": "Score", "desc": "Adds score bonus", "color": (255, 128, 0)},
        {"name": "Laser", "desc": "Shoots a laser beam", "color": (50, 150, 255)},
        {"name": "Slow", "desc": "Slows down balls", "color": (0, 200, 200)}
    ]
    
    for powerup in powerups:
        pygame.draw.ellipse(screen, powerup["color"], pygame.Rect(GAME_WIDTH + 20, legend_y, 15, 15))
        screen.blit(font.render(f"{powerup['name']}: {powerup['desc']}", True, WHITE), 
                  (GAME_WIDTH + 45, legend_y - 2))
        legend_y += 22  # Reduced spacing

# ---------------------------- MAIN GAME LOOP ----------------------------
def main():
    global balls, last_ball_mult_time, bricks
    global breakable_brick_count, level_reset_timer, level_reset_active
    global showing_round_summary, round_summary_start_time
    global player_brick_stats, ai_brick_stats, player_balls_lost, ai_balls_lost
    global player_round_score, ai_round_score, player_total_score, ai_total_score
    global round_winner, round_number

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

        if showing_round_summary:
            # Wait for SPACE key to continue or timeout after 15 seconds
            current_time = pygame.time.get_ticks()
            keys = pygame.key.get_pressed()
            
            # Redraw the round summary screen on each frame
            # First clear the screen
            screen.fill(BLACK, pygame.Rect(0, 0, GAME_WIDTH, SCREEN_HEIGHT))
            
            # Re-render the summary content
            # Draw title
            title_text = large_font.render(f"ROUND {round_number} SUMMARY", True, WHITE)
            title_rect = title_text.get_rect(center=(GAME_WIDTH//2, 60))
            screen.blit(title_text, title_rect)
            
            # Draw divider line
            pygame.draw.line(screen, WHITE, (GAME_WIDTH//2, 120), (GAME_WIDTH//2, 550), 2)
            
            # ----------- PLAYER STATS SECTION -----------
            # Draw player stats header
            player_header = large_font.render("PLAYER", True, BLUE)
            player_header_rect = player_header.get_rect(center=(GAME_WIDTH//4, 140))
            screen.blit(player_header, player_header_rect)
            
            # Calculate player score for display
            player_score_from_bricks = (player_brick_stats.get(1, 0) * 1 + 
                                     player_brick_stats.get(2, 0) * 3 + 
                                     player_brick_stats.get(3, 0) * 5 +
                                     player_brick_stats.get(4, 0) * 10 +
                                     player_brick_stats.get(5, 0) * 3)
            
            player_ball_penalty = min(15, sum(max(0, 6-i) for i in range(1, player_balls_lost+1)))
            
            # Draw player stats in a more organized way
            y_offset = 190
            line_spacing = 30
            
            # Brick breakdown
            screen.blit(font.render("BRICKS BROKEN:", True, WHITE), (50, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"Type 1 (1pt): {player_brick_stats.get(1, 0)} = {player_brick_stats.get(1, 0) * 1} pts", 
                      True, WHITE), (70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"Type 2 (3pts): {player_brick_stats.get(2, 0)} = {player_brick_stats.get(2, 0) * 3} pts", 
                      True, WHITE), (70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"Type 3 (5pts): {player_brick_stats.get(3, 0)} = {player_brick_stats.get(3, 0) * 5} pts", 
                      True, WHITE), (70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"Boss (10pts): {player_brick_stats.get(4, 0)} = {player_brick_stats.get(4, 0) * 10} pts", 
                      True, WHITE), (70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"Moving (3pts): {player_brick_stats.get(5, 0)} = {player_brick_stats.get(5, 0) * 3} pts", 
                      True, WHITE), (70, y_offset))
            y_offset += line_spacing
            
            # Totals
            pygame.draw.line(screen, WHITE, (50, y_offset), (GAME_WIDTH//2 - 50, y_offset), 1)
            y_offset += line_spacing
            
            screen.blit(font.render(f"BRICK TOTAL: {player_score_from_bricks} pts", True, WHITE), 
                      (70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"BALLS LOST: {player_balls_lost} (Penalty: {player_ball_penalty} pts)", 
                      True, WHITE), (70, y_offset))
            y_offset += line_spacing
            
            pygame.draw.line(screen, WHITE, (50, y_offset), (GAME_WIDTH//2 - 50, y_offset), 1)
            y_offset += line_spacing
            
            screen.blit(font.render(f"ROUND SCORE: {player_round_score} pts", True, BLUE), 
                      (70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"TOTAL SCORE: {player_total_score} pts", True, BLUE), 
                      (70, y_offset))
            
            # ----------- AI STATS SECTION -----------
            # Mirror layout on right side
            ai_header = large_font.render("AI", True, RED)
            ai_header_rect = ai_header.get_rect(center=(GAME_WIDTH*3//4, 140))
            screen.blit(ai_header, ai_header_rect)
            
            # Calculate AI score for display
            ai_score_from_bricks = (ai_brick_stats.get(1, 0) * 1 + 
                                  ai_brick_stats.get(2, 0) * 3 + 
                                  ai_brick_stats.get(3, 0) * 5 +
                                  ai_brick_stats.get(4, 0) * 10 +
                                  ai_brick_stats.get(5, 0) * 3)
            
            ai_ball_penalty = min(15, sum(max(0, 6-i) for i in range(1, ai_balls_lost+1)))
            
            y_offset = 190
            
            # Brick breakdown
            screen.blit(font.render("BRICKS BROKEN:", True, WHITE), (GAME_WIDTH//2 + 50, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"Type 1 (1pt): {ai_brick_stats.get(1, 0)} = {ai_brick_stats.get(1, 0) * 1} pts", 
                      True, WHITE), (GAME_WIDTH//2 + 70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"Type 2 (3pts): {ai_brick_stats.get(2, 0)} = {ai_brick_stats.get(2, 0) * 3} pts", 
                      True, WHITE), (GAME_WIDTH//2 + 70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"Type 3 (5pts): {ai_brick_stats.get(3, 0)} = {ai_brick_stats.get(3, 0) * 5} pts", 
                      True, WHITE), (GAME_WIDTH//2 + 70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"Boss (10pts): {ai_brick_stats.get(4, 0)} = {ai_brick_stats.get(4, 0) * 10} pts", 
                      True, WHITE), (GAME_WIDTH//2 + 70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"Moving (3pts): {ai_brick_stats.get(5, 0)} = {ai_brick_stats.get(5, 0) * 3} pts", 
                      True, WHITE), (GAME_WIDTH//2 + 70, y_offset))
            y_offset += line_spacing
            
            # Totals
            pygame.draw.line(screen, WHITE, (GAME_WIDTH//2 + 50, y_offset), (GAME_WIDTH - 50, y_offset), 1)
            y_offset += line_spacing
            
            screen.blit(font.render(f"BRICK TOTAL: {ai_score_from_bricks} pts", True, WHITE), 
                      (GAME_WIDTH//2 + 70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"BALLS LOST: {ai_balls_lost} (Penalty: {ai_ball_penalty} pts)", 
                      True, WHITE), (GAME_WIDTH//2 + 70, y_offset))
            y_offset += line_spacing
            
            pygame.draw.line(screen, WHITE, (GAME_WIDTH//2 + 50, y_offset), (GAME_WIDTH - 50, y_offset), 1)
            y_offset += line_spacing
            
            screen.blit(font.render(f"ROUND SCORE: {ai_round_score} pts", True, RED), 
                      (GAME_WIDTH//2 + 70, y_offset))
            y_offset += line_spacing
            
            screen.blit(font.render(f"TOTAL SCORE: {ai_total_score} pts", True, RED), 
                      (GAME_WIDTH//2 + 70, y_offset))
            
            # ----------- WINNER ANNOUNCEMENT -----------
            winner_y = 580
            
            # Draw winner announcement with background
            if round_winner == "PLAYER":
                winner_text = large_font.render("PLAYER WINS THIS ROUND!", True, BLUE)
                bg_color = (0, 0, 100)
                winner_color = BLUE
            elif round_winner == "AI":
                winner_text = large_font.render("AI WINS THIS ROUND!", True, RED)
                bg_color = (100, 0, 0)
                winner_color = RED
            else:
                winner_text = large_font.render("THIS ROUND IS A TIE!", True, WHITE)
                bg_color = (70, 70, 70)
                winner_color = WHITE
            
            winner_rect = winner_text.get_rect(center=(GAME_WIDTH//2, winner_y))
            
            # Draw background box for winner text
            bg_rect = winner_rect.inflate(40, 20)
            pygame.draw.rect(screen, bg_color, bg_rect)
            pygame.draw.rect(screen, winner_color, bg_rect, 3)
            
            # Draw winner text
            screen.blit(winner_text, winner_rect)
            
            # ----------- CONTINUE PROMPT -----------
            continue_text = font.render("Press SPACE to continue to next round", True, WHITE)
            continue_rect = continue_text.get_rect(center=(GAME_WIDTH//2, winner_y + 60))
            
            # Blinking effect
            if (pygame.time.get_ticks() // 500) % 2 == 0:  # Blink every half second
                screen.blit(continue_text, continue_rect)
            
            # Draw the side panel as well
            draw_side_panel(screen, font, metrics)
            
            # Update display
            pygame.display.flip()
            
            # Check for continue condition after drawing
            if keys[pygame.K_SPACE] or (current_time - round_summary_start_time > 15000):  # 15 seconds timeout
                showing_round_summary = False
                round_number += 1
                reset_level(player_paddle, ai_paddle, level)
                player_paddle.rect.width = PADDLE_WIDTH
                ai_paddle.rect.width = PADDLE_WIDTH
            
            # Skip the rest of the game loop
            continue

        if game_state != "playing":
            # Clear the screen first
            screen.fill(BLACK, pygame.Rect(0, 0, GAME_WIDTH, SCREEN_HEIGHT))
            
            # Draw the game background to give context
            for y in range(0, SCREEN_HEIGHT, 4):
                color_value = 20 + (y / SCREEN_HEIGHT * 30)
                pygame.draw.rect(screen, (0, 0, color_value), pygame.Rect(0, y, GAME_WIDTH, 4))
            
            # Draw pause/game over screen
            if game_state == "paused":
                # Semi-transparent overlay
                overlay = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 128))
                screen.blit(overlay, (0, 0))
                
                # Pause text with background
                pause_text = large_font.render("PAUSED", True, WHITE)
                text_rect = pause_text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2))
                bg_rect = text_rect.inflate(40, 20)
                pygame.draw.rect(screen, (50, 50, 50), bg_rect)
                pygame.draw.rect(screen, WHITE, bg_rect, 3)
                screen.blit(pause_text, text_rect)
                
                # Add instruction
                instruction = font.render("Press P to continue", True, WHITE)
                inst_rect = instruction.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2 + 60))
                screen.blit(instruction, inst_rect)
            
            elif game_state == "game_over":
                # Semi-transparent overlay
                overlay = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                
                result = "YOU WIN!" if ai_lives <= 0 else "GAME OVER"
                result_color = BLUE if ai_lives <= 0 else RED
                
                game_over_text = large_font.render(result, True, result_color)
                text_rect = game_over_text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2 - 50))
                bg_rect = text_rect.inflate(40, 20)
                pygame.draw.rect(screen, (50, 50, 50), bg_rect)
                pygame.draw.rect(screen, result_color, bg_rect, 3)
                screen.blit(game_over_text, text_rect)
                
                # Show final scores
                final_score_text = font.render(f"Final Score - Player: {player_total_score}  AI: {ai_total_score}", True, WHITE)
                score_rect = final_score_text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2 + 20))
                screen.blit(final_score_text, score_rect)
                
                restart_text = font.render("Press R to restart", True, WHITE)
                restart_rect = restart_text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2 + 60))
                screen.blit(restart_text, restart_rect)
            
            # Always draw the side panel for additional info
            draw_side_panel(screen, font, metrics)
            
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
                ai_balls_lost += 1  # Increment AI ball loss counter
                if lost_sound:
                    lost_sound.play()
                # Create explosion effect
                effects.append({"type": "explosion", "x": ball.rect.centerx, "y": ball.rect.centery, 
                              "radius": 10, "max_radius": 40, "color": RED})
                balls.remove(ball)
                if len(balls) == 0:
                    # Show round summary before resetting
                    show_round_summary(screen, font, large_font)
                    if ai_balls_lost >= 5:  # Max penalty for 5 balls lost
                        game_state = "game_over"
                continue
                
            if ball.rect.bottom >= SCREEN_HEIGHT:
                player_balls_lost += 1  # Increment player ball loss counter
                if lost_sound:
                    lost_sound.play()
                # Create explosion effect
                effects.append({"type": "explosion", "x": ball.rect.centerx, "y": ball.rect.centery, 
                              "radius": 10, "max_radius": 40, "color": BLUE})
                balls.remove(ball)
                if len(balls) == 0:
                    # Show round summary before resetting
                    show_round_summary(screen, font, large_font)
                    if player_balls_lost >= 5:  # Max penalty for 5 balls lost
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
                ball.last_hit_by = "player"  # Set last hit by player
                if hit_sound:
                    hit_sound.play()

            # Collision with AI paddle (only when ball is moving upward)
            if ball.rect.colliderect(ai_paddle.rect) and ball.vy < 0:
                ball.vy = abs(ball.vy)
                offset = (ball.rect.centerx - ai_paddle.rect.centerx) / (ai_paddle.rect.width / 2)
                ball.vx = INITIAL_BALL_SPEED * offset * 1.5
                # Reposition ball below paddle
                ball.rect.top = ai_paddle.rect.bottom
                ball.last_hit_by = "ai"  # Set last hit by AI
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
                        # Update brick stats based on who hit the ball last
                        if ball.last_hit_by == "player":
                            player_brick_stats[brick.type] = player_brick_stats.get(brick.type, 0) + 1
                        else:
                            ai_brick_stats[brick.type] = ai_brick_stats.get(brick.type, 0) + 1
                        
                        bricks.remove(brick)
                        score += 10 * level  # Keep this for overall game scoring
                        # Create enhanced particle effect
                        for _ in range(15):
                            effects.append({
                                "type": "particle",
                                "x": brick.rect.centerx,
                                "y": brick.rect.centery,
                                "vx": random.uniform(-4, 4),
                                "vy": random.uniform(-4, 4),
                                "life": 40,
                                "size": random.randint(2, 6),
                                "color": brick.color
                            })
                        # Chance to spawn power-up in the direction of the last player who hit the ball
                        if random.random() < 0.25:
                            direction = "down" if ball.last_hit_by == "player" else "up"
                            power_ups.append(PowerUp(brick.rect.centerx, brick.rect.centery, direction))
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
            if power_up.rect.colliderect(player_paddle.rect) and power_up.direction == "down":
                player_bonus, _, score_bonus = power_up.apply(player_paddle, ai_paddle, balls, "player")
                player_lives += player_bonus
                player_total_score += score_bonus  # Add score bonus to player total
                power_ups.remove(power_up)
                if powerup_sound:
                    powerup_sound.play()
                continue
                
            # Check if power-up is collected by AI
            if power_up.rect.colliderect(ai_paddle.rect) and power_up.direction == "up":
                _, ai_bonus, score_bonus = power_up.apply(player_paddle, ai_paddle, balls, "ai")
                ai_lives += ai_bonus
                ai_total_score += score_bonus  # Add score bonus to AI total
                power_ups.remove(power_up)
                if powerup_sound:
                    powerup_sound.play()
                continue
                
            # Remove if off-screen
            if (power_up.direction == "down" and power_up.rect.top > SCREEN_HEIGHT) or \
               (power_up.direction == "up" and power_up.rect.bottom < 0):
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
            elif effect["type"] == "text":
                text_surface = large_font.render(effect["text"], True, effect["color"])
                screen.blit(text_surface, (effect["x"] - text_surface.get_width()//2, effect["y"]))
                effect["life"] -= 1
                if effect["life"] <= 0:
                    effects.remove(effect)

        # --- Check Level Completion ---
        if len(bricks) == 0:
            level += 1
            show_round_summary(screen, font, large_font)
            # Reset will be handled after the summary display

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

        # Calculate remaining breakable bricks
        current_breakable_count = sum(1 for brick in bricks if brick.hits > 0)

        # Check if 80% of breakable bricks are cleared
        if not level_reset_active and breakable_brick_count > 0:
            if current_breakable_count <= 0.2 * breakable_brick_count:
                level_reset_active = True
                level_reset_timer = current_time
                # Create a visual notification
                effects.append({
                    "type": "text",
                    "text": "Level Advancing in 30s",
                    "x": GAME_WIDTH // 2,
                    "y": SCREEN_HEIGHT // 2,
                    "life": 180,
                    "size": 40,
                    "color": (255, 255, 0)
                })

        # If timer is active, check if it's been 30 seconds
        if level_reset_active:
            time_to_next = max(0, 30 - (current_time - level_reset_timer) // 1000)
            
            # Add countdown to metrics
            metrics["Next Level In"] = f"{time_to_next}s"
            
            if current_time - level_reset_timer >= 30000:  # 30 seconds
                level += 1
                show_round_summary(screen, font, large_font)
                level_reset_active = False

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
            elif effect["type"] == "text":
                text_surface = large_font.render(effect["text"], True, effect["color"])
                screen.blit(text_surface, (effect["x"] - text_surface.get_width()//2, effect["y"]))
                effect["life"] -= 1
                if effect["life"] <= 0:
                    effects.remove(effect)

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
