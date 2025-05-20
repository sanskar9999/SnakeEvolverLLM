import random

def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    if not my_snake.is_alive: return my_snake.direction_idx
    valid_actions = my_snake.get_valid_actions()
    if not valid_actions: return my_snake.direction_idx

    head_pos = my_snake.get_head_position()
    opponent_alive = opponent_snake.is_alive if opponent_snake else False

    def minimal_distance(pos1, pos2):
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        dx = min(dx, grid_width - dx)
        dy = min(dy, grid_height - dy)
        return dx + dy

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
    if not possible_actions: return my_snake.direction_idx

    if not foods: return random.choice(possible_actions)

    food_pos = foods[0].position

    best_action = None
    min_dist = float('inf')

    for action in possible_actions:
        dx_act, dy_act = my_snake.DIRECTIONS_MAP[action]
        new_pos = ((head_pos[0] + dx_act) % grid_width, (head_pos[1] + dy_act) % grid_height)
        dist = minimal_distance(new_pos, food_pos)

        if dist < min_dist:
            min_dist = dist
            best_action = action

    if opponent_alive and my_snake.length > opponent_snake.length:
        if head_pos in opponent_snake.positions:
            opposite_direction = 1 - my_snake.direction_idx
            opposite_action = my_snake.DIRECTIONS_MAP.index(my_snake.DIRECTIONS_MAP[opposite_direction])
            if opposite_action in possible_actions:
                return opposite_action

    if best_action:
        return best_action

    if opponent_alive and my_snake.length == opponent_snake.length:
        if head_pos in opponent_snake.positions:
            opposite_direction = 1 - my_snake.direction_idx
            opposite_action = my_snake.DIRECTIONS_MAP.index(my_snake.DIRECTIONS_MAP[opposite_direction])
            if opposite_action in possible_actions:
                return opposite_action

    # Outmaneuver the opponent by turning in the opposite direction
    if opponent_alive and len(possible_actions) > 1:
        opposite_direction = 1 - my_snake.direction_idx
        opposite_action = my_snake.DIRECTIONS_MAP.index(my_snake.DIRECTIONS_MAP[opposite_direction])
        if opposite_action in possible_actions:
            return opposite_action

    return random.choice(possible_actions)