# 🧱 Brick Versus - Enhanced Edition

A dynamic two-player brick breaking game where you compete against an AI opponent to destroy bricks and score points. Both players have paddles and must prevent balls from going past them while trying to break as many bricks as possible.

![Game Preview](https://via.placeholder.com/800x400?text=Brick+Versus+Screenshot)

## 📋 Table of Contents
- [Installation](#installation)
- [How to Play](#how-to-play)
- [Game Mechanics](#game-mechanics)
- [Scoring System](#scoring-system)
- [Power-ups](#power-ups)
- [Brick Types](#brick-types)
- [Level Design](#level-design)
- [Round System](#round-system)
- [Game States](#game-states)
- [AI Opponent](#ai-opponent)
- [Visual Effects](#visual-effects)
- [Tips and Strategies](#tips-and-strategies)

## 🔧 Installation

### Prerequisites
- Python 3.6 or higher
- Pygame library

### Setup
1. Clone or download this repository
2. Install Pygame if you don't have it already:
```
pip install pygame
```
3. Optional: For sound effects, place the following WAV files in the game directory:
   - `hit.wav` - Ball hitting paddle sound
   - `brick.wav` - Brick destruction sound
   - `lost.wav` - Ball lost sound
   - `powerup.wav` - Power-up collection sound

### Running the Game
Run the game by executing:
```
python multi_brick.py
```

## 🎮 How to Play

### Controls
- **Left Arrow**: Move paddle left
- **Right Arrow**: Move paddle right
- **P**: Pause/Unpause the game
- **R**: Restart the game (only when game over)
- **Space**: Continue to next round (after round summary)

### Basic Gameplay
1. You control the paddle at the bottom of the screen
2. The AI controls the paddle at the top
3. Break bricks by hitting them with the ball
4. Prevent balls from going past your paddle
5. Collect power-ups to gain advantages
6. Complete rounds by destroying bricks or outscoring the AI
7. Game continues until a player loses (loses 5 or more balls)

## 🔄 Game Mechanics

### Ball Physics
- Balls bounce off paddles, walls, and bricks
- Ball angle changes based on where it hits the paddle
- Ball speed gradually increases throughout the game
- Every 30 seconds, each ball in play spawns a duplicate (up to max 6 balls)
- Balls remember which player last hit them (for scoring purposes)

### Paddles
- Player paddle: Controlled by arrow keys
- AI paddle: Automatically tracks and tries to hit balls
- Paddle size can be increased with power-ups
- Paddle speed: 20 pixels per frame

### Ball Loss
- When a ball goes past your paddle, you lose it
- Losing balls incurs a score penalty
- If you lose 5 balls in a round, you lose the game
- When all balls are lost, the round ends

## 📊 Scoring System

### Brick Points
| Brick Type | Description | Points |
|------------|-------------|--------|
| Type 1 (Blue) | Basic brick | 1 point |
| Type 2 (Red) | Tough brick | 3 points |
| Type 3 (Gray) | Unbreakable brick | 5 points |
| Type 4 (Gold) | Boss brick | 10 points |
| Type 5 (Teal) | Moving brick | 3 points |

### Ball Loss Penalties
- Each lost ball incurs a penalty that decreases with each subsequent loss:
  - 1st ball lost: -5 points
  - 2nd ball lost: -4 points
  - 3rd ball lost: -3 points
  - 4th ball lost: -2 points
  - 5th ball lost: -1 point
- Maximum penalty per round: 15 points

### Round Score Calculation
```
Round Score = (Points from broken bricks) - (Ball loss penalty)
```
- If calculated score is negative, it's set to 0

### Total Score
- Total score is the sum of all round scores
- The player with the higher total score at game end is the overall winner

## 🌈 Power-ups

Power-ups randomly spawn when breaking bricks (25% chance). The power-up direction determines which player can collect it.

| Power-up | Color | Effect |
|----------|-------|--------|
| Speed | Yellow | Increases all balls' velocity by 10% |
| Size | Green | Increases collector's paddle width by 20% (max 200%) |
| Multi | Purple | Adds a new ball near an existing one |
| Score | Orange | Adds 20 points to collector's score |
| Laser | Light Blue | Shoots a laser beam that destroys bricks in its path |
| Slow | Teal | Decreases all balls' velocity by 30% |

- Power-ups moving downward can be collected by the player
- Power-ups moving upward can be collected by the AI
- A notification appears when a power-up is collected

## 🧱 Brick Types

### Basic Bricks (Blue)
- Requires 1 hit to break
- Worth 1 point
- Most common brick type

### Tough Bricks (Red)
- Requires 3 hits to break
- Darkens with each hit
- Worth 3 points
- More common in higher levels

### Unbreakable Bricks (Gray)
- Cannot be broken by normal means
- Can only be destroyed by laser power-up
- Worth 5 points
- Used for level design structure

### Boss Bricks (Gold)
- Appears on level 3 and every 3rd level after
- Requires many hits to break (2 × current level)
- Twice the width of normal bricks
- Worth 10 points
- Changes color as it takes damage

### Moving Bricks (Teal)
- Moves horizontally, bouncing off walls
- Requires 2 hits to break
- Worth 3 points
- Adds dynamic challenge

## 🏗️ Level Design

The game features 5 different brick layouts that rotate as levels progress:

### 1. Standard Pattern (Level % 5 == 0)
- Random distribution of bricks
- 85% chance for each brick position to contain a brick
- Higher levels have more tough and unbreakable bricks

### 2. Checkerboard Pattern (Level % 5 == 1)
- Alternating brick placement
- Outer edge bricks are always breakable
- Inner bricks may sometimes be unbreakable (10% chance)

### 3. Fortress Pattern (Level % 5 == 2)
- Border of tough bricks surrounding the playfield
- Strategic breakable "entrance points" on each side
- 60% chance for interior bricks to appear

### 4. Triangle Pattern (Level % 5 == 3)
- Bricks arranged in a triangular formation
- Mix of brick types with increasing difficulty

### 5. Circular Pattern (Level % 5 == 4)
- Concentric rings of bricks
- Outer ring: Type 1 (easy) bricks
- Middle ring: Type 2 (medium) bricks
- Inner ring: Type 3 (unbreakable) bricks

### Level Advancement
- Level advances automatically when 80% of breakable bricks are cleared
- 30-second countdown timer appears when threshold is reached
- A round summary appears after level completion
- Difficulty increases with level:
  - Higher levels have more tough bricks
  - Boss bricks appear more frequently and require more hits

## 🔄 Round System

### Round Flow
1. Round begins with player and AI each having one ball
2. Players break bricks and try to prevent ball loss
3. Round ends when:
   - All balls are lost
   - All bricks are destroyed
   - 80% of breakable bricks are cleared and 30-second timer expires
4. Round summary displays showing points earned and winner
5. Next round begins with reset level and paddles

### Round Summary
The round summary screen shows:
- Bricks broken by each player (with point breakdown)
- Balls lost by each player (with penalty breakdown)
- Round score calculation
- Total cumulative score
- Round winner announcement
- Press SPACE to continue to next round

## 🎭 Game States

### Playing
- Normal gameplay
- Side panel shows current stats and information

### Paused
- Game is temporarily suspended
- "PAUSED" overlay appears
- Press P to resume

### Round Summary
- Displays after each round
- Shows detailed breakdown of scoring
- Automatically advances after 15 seconds or press SPACE

### Game Over
- Occurs when player or AI loses 5 or more balls
- Shows final scores and winner
- Press R to restart

## 🤖 AI Opponent

The AI opponent controls the top paddle with these behaviors:

### Target Selection
- Focuses on the ball closest to its paddle vertically
- Ignores other balls until the target is out of range

### Movement Logic
- Moves left or right to align paddle center with target ball
- Uses same paddle speed as player (20 pixels per frame)
- No "look ahead" prediction - reacts to current ball position

### Power-up Collection
- Can collect power-ups moving upward
- Gets the same benefits as the player would
- Competes for advantageous power-ups

## ✨ Visual Effects

### Ball Trails
- Each ball leaves a fading trail showing its recent path
- Trail length: 5 positions
- Opacity decreases with distance

### Brick Destruction Particles
- 15 colorful particles spawn when a brick is destroyed
- Particles match the brick's color
- Random velocity and size for organic effect

### Explosion Effects
- Visual feedback when balls are lost
- Expanding circle with fading opacity

### Laser Effects
- Temporary beam creates a glowing effect
- Visual text shows how many bricks were destroyed

### Power-up Effects
- Pulsing glow around power-ups
- Color-coded for easy identification
- Notification text when collected

### 3D Brick Effects
- Light edges (top/left) and dark edges (bottom/right)
- Creates illusion of depth

## 💡 Tips and Strategies

1. **Ball Angle Control**: The ball's bounce angle depends on where it hits your paddle. Hit with the edge for sharper angles.

2. **Power-up Prioritization**: The "Multi" and "Size" power-ups are particularly valuable - position your paddle to collect these when possible.

3. **Strategic Brick Breaking**: 
   - Focus on creating paths to higher-value bricks
   - Target moving and boss bricks for higher points
   - Use the laser power-up to cut through unbreakable bricks

4. **Ball Management**: With multiple balls in play, prioritize saving the ball closest to your paddle.

5. **AI Weaknesses**: The AI struggles with:
   - Very fast balls
   - Multiple balls spread across the screen
   - Extreme bounce angles

6. **Level Advancement**: Use the 30-second countdown period to maximize your score before the level resets.

7. **Penalty Minimization**: Try to minimize ball losses as the penalties can significantly impact your score.

8. **Score Optimization**: Break as many high-value bricks as possible while maintaining ball control.

---

## 🎮 Enjoy Brick Versus!

This game combines classic brick-breaking gameplay with competitive AI elements and a rich scoring system. Challenge yourself to master the game mechanics and outperform the AI opponent across multiple rounds!
