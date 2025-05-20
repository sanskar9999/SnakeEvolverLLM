import random
from collections import deque


def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    valid_actions = my_snake.get_valid_actions()
    if not valid_actions:
        return my_snake.direction_idx

    head_pos = my_snake.get_head_position()

    # Check if opponent is alive
    opponent_alive = opponent_snake.is_alive if opponent_snake else False

    # If opponent is dead, focus on food
    if not opponent_alive:
        if foods:
            food_pos = foods[0].position
            dx = (food_pos[0] - head_pos[0]) % grid_width
            dy = (food_pos[1] - head_pos[1]) % grid_height

            # Choose direction based on food position
            if dx > dy:
                preferred_direction = 1 if dx > 0 else 3
            else:
                preferred_direction = 0 if dy > 0 else 2

            if preferred_direction in valid_actions:
                return preferred_direction
        return random.choice(valid_actions)

    # If opponent is alive, get their head position
    opponent_head = opponent_snake.get_head_position()
    dx_opponent = abs(head_pos[0] - opponent_head[0])
    dy_opponent = abs(head_pos[1] - opponent_head[1])
    distance_to_opponent = dx_opponent + dy_opponent

    # If close to opponent, prioritize blocking
    if distance_to_opponent < 5:
        if foods:
            food_pos = foods[0].position
            dx_food = (food_pos[0] - opponent_head[0]) % grid_width
            dy_food = (food_pos[1] - opponent_head[1]) % grid_height

            # Determine best blocking direction
            if dx_food > dy_food:
                preferred_direction = 1 if dx_food > 0 else 3
            else:
                preferred_direction = 0 if dy_food > 0 else 2

            if preferred_direction in valid_actions:
                return preferred_direction

        # If no food, focus on maintaining distance
        possible_moves = []
        for action in valid_actions:
            dx, dy = my_snake.DIRECTIONS_MAP[action]
            new_pos = ((head_pos[0] + dx) % grid_width, (head_pos[1] + dy) % grid_height)
            new_distance = abs(new_pos[0] - opponent_head[0]) + abs(new_pos[1] - opponent_head[1])
            possible_moves.append((new_distance, action))

        # Sort by descending distance to maximize separation
        possible_moves.sort(reverse=True)
        return possible_moves[0][1]

    # If not close to opponent, focus on food and growth
    if foods:
        food_pos = foods[0].position
        dx_food = (food_pos[0] - head_pos[0]) % grid_width
        dy_food = (food_pos[1] - head_pos[1]) % grid_height

        # Prefer moving in direction of food
        if dx_food > dy_food:
            preferred_direction = 1 if dx_food > 0 else 3
        else:
            preferred_direction = 0 if dy_food > 0 else 2

        if preferred_direction in valid_actions:
            return preferred_direction

    # Default to random valid action
    return random.choice(valid_actions)