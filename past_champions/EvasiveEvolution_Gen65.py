import random
from collections import deque

def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    valid_actions = my_snake.get_valid_actions()
    if not valid_actions: return my_snake.direction_idx

    head_pos = my_snake.get_head_position()
    opponent_alive = opponent_snake.is_alive if opponent_snake else False

    if not opponent_alive:
        if foods:
            food_pos = foods[0].position
            dx = (food_pos[0] - head_pos[0]) % grid_width
            dy = (food_pos[1] - head_pos[1]) % grid_height
            if dx > dy:
                preferred = 1 if dx > 0 else 3
            else:
                preferred = 0 if dy > 0 else 2
            if preferred in valid_actions:
                return preferred
        return random.choice(valid_actions)

    opponent_head = opponent_snake.get_head_position()
    dx_op = abs(head_pos[0] - opponent_head[0])
    dy_op = abs(head_pos[1] - opponent_head[1])
    distance_to_opponent = dx_op + dy_op

    if distance_to_opponent < 5:
        if foods:
            food_pos = foods[0].position
            dx_food = abs(food_pos[0] - opponent_head[0])
            dy_food = abs(food_pos[1] - opponent_head[1])
            if dx_food < dy_food:
                preferred = 0 if dy_food > 0 else 2
            else:
                preferred = 1 if dx_food > 0 else 3
            if preferred in valid_actions:
                return preferred
        possible_moves = []
        for action in valid_actions:
            dx, dy = my_snake.DIRECTIONS_MAP[action]
            new_pos = ((head_pos[0] + dx) % grid_width, (head_pos[1] + dy) % grid_height)
            new_distance = abs(new_pos[0] - opponent_head[0]) + abs(new_pos[1] - opponent_head[1])
            possible_moves.append((new_distance, action))
        possible_moves.sort(reverse=True)
        return possible_moves[0][1]

    if foods:
        food_pos = foods[0].position
        dx_food = (food_pos[0] - head_pos[0]) % grid_width
        dy_food = (food_pos[1] - head_pos[1]) % grid_height
        if dx_food > dy_food:
            preferred = 1 if dx_food > 0 else 3
        else:
            preferred = 0 if dy_food > 0 else 2
        if preferred in valid_actions:
            return preferred

    # Prefer the action that keeps the opponent at the greatest distance
    opponent_distances = []
    for action in valid_actions:
        dx, dy = my_snake.DIRECTIONS_MAP[action]
        new_pos = ((head_pos[0] + dx) % grid_width, (head_pos[1] + dy) % grid_height)
        new_distance = abs(new_pos[0] - opponent_head[0]) + abs(new_pos[1] - opponent_head[1])
        opponent_distances.append((new_distance, action))
    opponent_distances.sort(reverse=True)
    return opponent_distances[0][1]