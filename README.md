# Breakout RL Agent

This project implements a **Deep Q-Network (DQN)** to train an AI agent to play a simple **Breakout**-like game using **Reinforcement Learning (RL)**. The game is built using **Pygame**, and the DQN model is implemented using **TensorFlow**.

---

## 🚀 Reinforcement Learning Algorithm: Deep Q-Network (DQN)

### 🎯 Overview
The agent learns to play the game by interacting with the environment and updating a neural network to approximate the **Q-value function**, which helps it make optimal decisions.

### 🔍 Key Components

1. **State Representation**
   - The state is represented as a set of key features from the game, including the ball’s position, velocity, and paddle position.

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
