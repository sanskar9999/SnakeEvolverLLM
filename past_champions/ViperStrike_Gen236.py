import random

def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    valid_actions = my_snake.get_valid_actions()
    if not valid_actions:
        return my_snake.direction_idx

    head_pos = my_snake.get_head_position()
    opponent_alive = opponent_snake.is_alive if opponent_snake else False

    def is_collision(action):
        dx, dy = my_snake.DIRECTIONS_MAP[action]
        new_x = (head_pos[0] + dx) % grid_width
        new_y = (head_pos[1] + dy) % grid_height
        if (new_x, new_y) in my_snake.positions:
            return True
        if opponent_alive and (new_x, new_y) in opponent_snake.positions:
            return True
        return False

    possible_actions = [action for action in valid_actions if not is_collision(action)]
    if not possible_actions:
        return my_snake.direction_idx

    if not opponent_alive:
        if foods:
            food_pos = foods[0].position
            dx = (food_pos[0] - head_pos[0]) % grid_width
            dy = (food_pos[1] - head_pos[1]) % grid_height
            if dx > dy:
                preferred = 1 if dx > 0 else 3
            else:
                preferred = 0 if dy > 0 else 2
            if preferred in possible_actions:
                return preferred
        return random.choice(possible_actions)

    else:
        if my_snake.length > opponent_snake.length:
            opponent_head = opponent_snake.get_head_position()
            dx = (opponent_head[0] - head_pos[0]) % grid_width
            dy = (opponent_head[1] - head_pos[1]) % grid_height
            if dx > dy:
                preferred = 1 if dx > 0 else 3
            else:
                preferred = 0 if dy > 0 else 2
            if preferred in possible_actions:
                return preferred
            best_action = None
            best_distance = float('inf')
            for action in possible_actions:
                dx_a, dy_a = my_snake.DIRECTIONS_MAP[action]
                new_x = (head_pos[0] + dx_a) % grid_width
                new_y = (head_pos[1] + dy_a) % grid_height
                distance = abs(new_x - opponent_head[0]) + abs(new_y - opponent_head[1])
                if distance < best_distance:
                    best_distance = distance
                    best_action = action
            return best_action
        else:
            if foods:
                food_pos = foods[0].position
                dx = (food_pos[0] - head_pos[0]) % grid_width
                dy = (food_pos[1] - head_pos[1]) % grid_height
                if dx > dy:
                    preferred = 1 if dx > 0 else 3
                else:
                    preferred = 0 if dy > 0 else 2
                if preferred in possible_actions:
                    return preferred
            best_action = None
            max_distance = -1
            for action in possible_actions:
                dx_a, dy_a = my_snake.DIRECTIONS_MAP[action]
                new_x = (head_pos[0] + dx_a) % grid_width
                new_y = (head_pos[1] + dy_a) % grid_height
                distance = abs(new_x - opponent_head[0]) + abs(new_y - opponent_head[1])
                if distance > max_distance:
                    max_distance = distance
                    best_action = action
            return best_action