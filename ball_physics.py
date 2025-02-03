import math
import numpy as np
import pygame

# -----------------------------
# Helper functions
# -----------------------------
def rotate_point(point, angle, center):
    """
    Rotate a 2D point around a given center by 'angle' radians.
    """
    s, c = math.sin(angle), math.cos(angle)
    translated = point - center
    rotated = np.array([translated[0]*c - translated[1]*s,
                        translated[0]*s + translated[1]*c])
    return rotated + center

def closest_point_on_segment(A, B, P):
    """
    Returns the closest point on the line segment AB to point P.
    """
    AB = B - A
    if np.allclose(AB, 0):
        return A
    t = np.dot(P - A, AB) / np.dot(AB, AB)
    t = np.clip(t, 0, 1)
    return A + t * AB

def compute_inward_normal(A, B, poly_center):
    """
    Compute the inward normal (unit vector) for edge AB of a polygon,
    ensuring that the normal points from the edge toward the polygon’s center.
    """
    # Compute candidate normal: rotate edge vector by 90 degrees
    edge = B - A
    candidate = np.array([edge[1], -edge[0]])
    candidate_norm = candidate / np.linalg.norm(candidate)
    # Ensure it points toward the polygon center.
    mid = (A + B) / 2.0
    if np.dot(poly_center - mid, candidate_norm) < 0:
        candidate_norm = -candidate_norm
    return candidate_norm

# -----------------------------
# Main simulation
# -----------------------------
def main():
    # Initialize Pygame
    pygame.init()
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ball in a Rotating Hexagon")
    clock = pygame.time.Clock()
    running = True

    # -----------------------------
    # Simulation parameters
    # -----------------------------
    # Physics constants
    gravity = np.array([0, 500.0])  # pixels/s^2 (downward)
    restitution = 0.9               # bounce factor (0 < restitution <= 1)
    friction_coef = 0.2             # friction coefficient for tangential velocity

    # Ball properties
    ball_radius = 15
    ball_position = np.array([WIDTH/2, HEIGHT/2])
    ball_velocity = np.array([200.0, -150.0])  # initial velocity in pixels/s

    # Hexagon properties
    hex_center = np.array([WIDTH/2, HEIGHT/2])
    hex_radius = 200              # distance from center to vertex
    hexagon_local = []            # vertices in local (non-rotated) coordinates
    num_sides = 6
    for i in range(num_sides):
        angle = 2 * math.pi * i / num_sides
        vertex = np.array([hex_radius * math.cos(angle),
                           hex_radius * math.sin(angle)])
        hexagon_local.append(vertex)
    hexagon_local = np.array(hexagon_local)

    hex_angle = 0.0                           # initial rotation angle in radians
    hex_angular_velocity = math.radians(30)   # constant angular velocity (30°/s)

    # -----------------------------
    # Main loop
    # -----------------------------
    while running:
        dt = clock.tick(60) / 1000.0  # seconds elapsed since last frame (aim for 60 FPS)

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Update Hexagon ---
        hex_angle += hex_angular_velocity * dt

        # Compute the global (rotated) positions of the hexagon vertices.
        hexagon_global = []
        for vertex in hexagon_local:
            # Since the local vertices are relative to hex_center, we can
            # rotate them directly and then add hex_center.
            s, c = math.sin(hex_angle), math.cos(hex_angle)
            rotated = np.array([vertex[0]*c - vertex[1]*s,
                                vertex[0]*s + vertex[1]*c])
            hexagon_global.append(rotated + hex_center)
        hexagon_global = np.array(hexagon_global)

        # --- Update Ball Physics ---
        # Apply gravity
        ball_velocity += gravity * dt
        # Update position
        ball_position += ball_velocity * dt

        # --- Collision Detection & Response with Hexagon Edges ---
        for i in range(len(hexagon_global)):
            A = hexagon_global[i]
            B = hexagon_global[(i + 1) % len(hexagon_global)]
            # Compute the inward normal for this edge.
            n = compute_inward_normal(A, B, hex_center)

            # Find the closest point on the edge AB to the ball’s center.
            closest = closest_point_on_segment(A, B, ball_position)
            diff = ball_position - closest
            dist = np.linalg.norm(diff)

            if dist < ball_radius:
                # --- Position Correction ---
                penetration = ball_radius - dist
                # Use the diff direction if available; otherwise fall back on edge normal.
                if dist != 0:
                    correction_dir = diff / dist
                else:
                    correction_dir = n
                ball_position += correction_dir * penetration

                # --- Collision Response ---
                # Compute the velocity of the wall at the collision point due to rotation.
                r = closest - hex_center
                # In 2D, the tangential velocity due to rotation: v = ω x r,
                # which can be computed as: v = ω * [-r_y, r_x]
                v_wall = hex_angular_velocity * np.array([-r[1], r[0]])

                # Compute the ball’s velocity relative to the wall.
                v_rel = ball_velocity - v_wall
                # Determine the component along the collision normal.
                v_rel_normal = np.dot(v_rel, n)

                # Only respond if the ball is moving into the wall.
                if v_rel_normal < 0:
                    # Decompose the relative velocity into normal and tangential components.
                    v_n = v_rel_normal * n
                    v_t = v_rel - v_n

                    # Reflect the normal component (with restitution) and reduce the tangential
                    # component according to friction.
                    v_n_new = -restitution * v_n
                    v_t_new = (1 - friction_coef) * v_t

                    # Update ball velocity by adding back the wall’s velocity.
                    ball_velocity = v_wall + v_n_new + v_t_new

        # --- Rendering ---
        screen.fill((30, 30, 30))  # Dark background

        # Draw the rotating hexagon.
        hex_points = [(int(x), int(y)) for x, y in hexagon_global]
        pygame.draw.polygon(screen, (200, 200, 200), hex_points, 3)

        # Draw the ball.
        pygame.draw.circle(screen, (255, 100, 100),
                           (int(ball_position[0]), int(ball_position[1])), ball_radius)

        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main()
