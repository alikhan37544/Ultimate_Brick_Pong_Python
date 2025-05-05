from brickpong_gym_env import BrickPongEnv

env = BrickPongEnv()
obs = env.reset()
print("Initial observation:", obs)

done = False
step_count = 0
while not done and step_count < 50:
    action = env.action_space.sample()  # Random action
    obs, reward, done, info = env.step(action)
    print(f"Step {step_count}: action={action}, reward={reward}, done={done}")
    step_count += 1

env.close()
print("Test finished.")