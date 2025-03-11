# Breakout RL Agent

This project implements a **Deep Q-Network (DQN)** to train an AI agent to play a simple **Breakout**-like game using **Reinforcement Learning (RL)**. The game is built using **Pygame**, and the DQN model is implemented using **TensorFlow**.

---

## 🎮 Game Overview: Brick Versus - Enhanced Edition

Brick Versus is an enhanced, two-player version of the classic Breakout game. You control a paddle at the bottom of the screen, while an AI controls a paddle at the top. Your goal is to destroy bricks and outlast your AI opponent.

### 🕹️ How to Play

- Use the **LEFT** and **RIGHT** arrow keys to move your paddle
- Prevent balls from going off the bottom of the screen
- Break bricks to score points
- Collect power-ups to gain advantages
- Beat the AI by making it lose all its lives first

### 📊 Game Metrics (Displayed in Side Panel)

- **Score**: Points earned by breaking bricks
- **Level**: Current game level (increases difficulty)
- **Player Lives**: Number of remaining player lives
- **AI Lives**: Number of remaining AI lives
- **Ball Count**: Number of balls currently in play
- **Ball Mult**: Countdown timer until next ball multiplication
- **AI Info**: Shows the AI's target ball and decision-making process

---

## 🌈 Power-Up System

Power-ups randomly spawn when breaking bricks. Each has a unique color and effect:

| Color | Type | Effect |
|-------|------|--------|
| **Yellow** 🟡 | Speed | Increases ball speed by 10% |
| **Green** 🟢 | Size | Increases paddle width by 20% |
| **Purple** 🟣 | Multi | Adds a new ball to the game |
| **Orange** 🟠 | Life | Adds an extra life |
| **Light Blue** 🔵 | Laser | Creates a temporary laser beam that destroys bricks |
| **Teal** 🧊 | Slow | Decreases ball speed by 30% |

Power-ups can benefit either the player or the AI depending on their direction of travel.

---

## 🧱 Brick Types and Level Design

### Brick Types

- **Blue Bricks**: Basic bricks (1 hit)
- **Red Bricks**: Tougher bricks (3 hits)
- **Gray Bricks**: Unbreakable bricks
- **Gold Bricks**: "Boss" bricks (many hits, appears on higher levels)
- **Teal Bricks**: Moving bricks that slide horizontally

### Level Designs

The game features five different level layouts:
1. **Standard Pattern**: Random brick distribution
2. **Checkerboard Pattern**: Alternating brick placement
3. **Fortress Pattern**: Tough outer wall with breakable interior
4. **Triangle Pattern**: Bricks arranged in triangle formation
5. **Circular Pattern**: Concentric rings of bricks (tougher toward center)

Level difficulty increases as you progress, with more tough and unbreakable bricks appearing. Level advances automatically when 80% of breakable bricks are cleared (30-second countdown).

---

## 🤖 AI Opponent Behavior

The AI paddle uses a simple tracking algorithm:

1. **Target Selection**: Identifies the ball closest to it vertically
2. **Position Tracking**: Moves left or right to align its center with the target ball
3. **Decision Making**: Updates position every frame based on the ball's location

The side panel displays the AI's current target information and decision (move left, right, or stay).

### AI Quirks
- The AI occasionally struggles with multiple balls, focusing on only one at a time
- It can be overwhelmed by fast-moving balls or unpredictable bounces
- The AI gets the same power-ups as the player, creating a balanced competition

---

## 🎯 Special Game Mechanics

- **Ball Multiplication**: Every 30 seconds, each ball in play spawns a duplicate with inverted horizontal velocity (limited to 6 maximum)
- **Level Advancement**: Automatically occurs after 30 seconds when 80% of breakable bricks are cleared
- **Ball Trails**: Visual effect showing the ball's recent path
- **Particle Effects**: Colorful particles when bricks are destroyed
- **Explosion Effects**: Visual feedback when balls are lost
- **Laser Effects**: Temporary beam that can destroy multiple bricks
- **3D Brick Effects**: Light/dark edges for visual depth

---

## 🚀 Reinforcement Learning Algorithm: Deep Q-Network (DQN)

### 🎯 Overview
The agent learns to play the game by interacting with the environment and updating a neural network to approximate the **Q-value function**, which helps it make optimal decisions.

### 🔍 Key Components

1. **State Representation**
   - The state is represented as a set of key features from the game, including the ball's position, velocity, and paddle position.

2. **Action Space**
   - The agent can take one of three actions:
     - Move Left
     - Move Right
     - Stay Still

3. **Reward Function**
   - The agent receives:
     - **Positive rewards** for hitting bricks.
     - **Negative rewards** for missing the ball.
     - **Small rewards** for surviving longer.

4. **Q-Learning Update Rule**
   - The Bellman equation is used to update the Q-values:
     \[
     Q(s, a) \leftarrow Q(s, a) + \alpha \Big( r + \gamma \max_{a'} Q(s', a') - Q(s, a) \Big)
     \]
   - Where:
     - \( \alpha \) is the learning rate.
     - \( \gamma \) is the discount factor.
     - \( r \) is the immediate reward.
     - \( Q(s, a) \) is the predicted Q-value for action \( a \) in state \( s \).

---

## 🧠 Neural Network Architecture

The DQN model is implemented as a **feedforward neural network** with the following structure:

- **Input Layer:** Takes in the game state vector.
- **Hidden Layers:** Two fully connected layers with ReLU activation.
- **Output Layer:** Predicts Q-values for each possible action.

### 📌 Model Summary:
- **Layer 1:** Dense (24 neurons, ReLU activation)
- **Layer 2:** Dense (24 neurons, ReLU activation)
- **Output:** Dense (3 neurons, Linear activation) → Represents Q-values for each action.

---

## 🎮 Training Process

1. **Experience Replay**
   - The agent stores past experiences in a replay buffer and trains on a random batch to improve learning stability.

2. **Exploration vs Exploitation**
   - Uses an **ε-greedy policy**:
     - With probability **ε**, the agent explores (chooses a random action).
     - Otherwise, it exploits the best known Q-values.
     - **ε decays** over time to encourage learning from experiences.

3. **Model Training**
   - The agent is trained using the **Adam optimizer** with Mean Squared Error (MSE) loss.
   - The training loop updates the Q-values based on the Bellman equation.

---

## 🔑 Controls & Game States

- **Arrow Keys**: Move paddle left/right
- **P Key**: Pause/resume game
- **R Key**: Restart game after game over

Game states include:
- **Playing**: Main gameplay
- **Paused**: Game temporarily suspended
- **Game Over**: Displayed when either player or AI loses all lives

---

## 💡 Tips and Strategies

1. **Power-up Management**: Try to position yourself to catch beneficial power-ups while avoiding the AI getting theirs
2. **Multi-ball Strategy**: With multiple balls, focus on the one closest to your paddle
3. **Brick Targeting**: Target "boss bricks" strategically as they give higher scores
4. **Ball Angle Control**: The ball's angle changes based on where it hits your paddle - use this to aim!
5. **Level Advancement**: Use the 30-second countdown to your advantage to prepare for the next level

---

## 🔊 Sound Effects

The game includes sound effects for enhanced gameplay experience:
- Ball hitting paddles
- Brick destruction
- Power-up collection
- Ball loss

Note: Sound files must be in the game directory for audio to work. The game will run without them if unavailable.

---
