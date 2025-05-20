import random
from collections import deque

Snake = None  # Placeholder for type hints, replace with actual Snake class if available


def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    valid_actions = my_snake.get_valid_actions()
    if not valid_actions:
        return my_snake.direction_idx

    head_pos = my_snake.get_head_position()
    opponent_alive = opponent_snake.is_alive if opponent_snake else False

    # Enhanced minimal distance calculation considering grid wrap
    def minimal_distance(pos1, pos2):
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        dx = min(dx, grid_width - dx)
        dy = min(dy, grid_height - dy)
        return dx + dy

    # Check for potential collisions with self or opponent
    def is_collision(action):
        dx, dy = my_snake.DIRECTIONS_MAP[action]
        new_x = (head_pos[0] + dx) % grid_width
        new_y = (head_pos[1] + dy) % grid_height
        if (new_x, new_y) in my_snake.positions:
            return True
        if opponent_alive and (new_x, new_y) in opponent_snake.positions:
            return True
        return False

    # Filter valid actions to avoid collisions
    possible_actions = [action for action in valid_actions if not is_collision(action)]
    if not possible_actions:
        return my_snake.direction_idx

    # If no opponent, focus solely on food
    if not opponent_alive:
        if foods:
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
            return best_action

    # Strategic decisions based on opponent's state
    opponent_head = opponent_snake.get_head_position()
    my_length = my_snake.length
    opponent_length = opponent_snake.length

    # Calculate relative position considering grid wrap
    dx_opponent = (opponent_head[0] - head_pos[0]) % grid_width
    dy_opponent = (opponent_head[1] - head_pos[1]) % grid_height

    # If longer than opponent, pursue aggressively
    if my_length > opponent_length:
        # Prefer moving towards the opponent's current position
        preferred = None
        if dx_opponent > dy_opponent:
            preferred = 1 if dx_opponent > 0 else 3
        else:
            preferred = 0 if dy_opponent > 0 else 2
        if preferred in possible_actions:
            return preferred
        # Find action that minimizes distance to opponent
        best_action = None
        min_dist = float('inf')
        for action in possible_actions:
            dx_act, dy_act = my_snake.DIRECTIONS_MAP[action]
            new_pos = ((head_pos[0] + dx_act) % grid_width, (head_pos[1] + dy_act) % grid_height)
            dist = minimal_distance(new_pos, opponent_head)
            if dist < min_dist:
                min_dist = dist
                best_action = action
        return best_action

    # If shorter than opponent, prioritize food and evasion
    elif my_length < opponent_length:
        if foods:
            food_pos = foods[0].position
            best_food_action = None
            min_food_dist = float('inf')
            for action in possible_actions:
                dx_act, dy_act = my_snake.DIRECTIONS_MAP[action]
                new_pos = ((head_pos[0] + dx_act) % grid_width, (head_pos[1] + dy_act) % grid_height)
                dist = minimal_distance(new_pos, food_pos)
                if dist < min_food_dist:
                    min_food_dist = dist
                    best_food_action = action
            if best_food_action:
                return best_food_action
        # Maximize distance from opponent
        best_evasion_action = None
        max_dist = -1
        for action in possible_actions:
            dx_act, dy_act = my_snake.DIRECTIONS_MAP[action]
            new_pos = ((head_pos[0] + dx_act) % grid_width, (head_pos[1] + dy_act) % grid_height)
            dist = minimal_distance(new_pos, opponent_head)
            if dist > max_dist:
                max_dist = dist
                best_evasion_action = action
        return best_evasion_action

    # When lengths are equal, focus on strategic positioning
    else:
        if foods:
            food_pos = foods[0].position
            best_food_action = None
            min_food_dist = float('inf')
            for action in possible_actions:
                dx_act, dy_act = my_snake.DIRECTIONS_MAP[action]
                new_pos = ((head_pos[0] + dx_act) % grid_width, (head_pos[1] + dy_act) % grid_height)
                dist = minimal_distance(new_pos, food_pos)
                if dist < min_food_dist:
                    min_food_dist = dist
                    best_food_action = action
            if best_food_action:
                return best_food_action

        # Alternate between aggressive and defensive strategies based on proximity
        current_dist = minimal_distance(head_pos, opponent_head)
        if current_dist < 5:
            # Evade by maximizing distance
            best_evasion_action = None
            max_dist = -1
            for action in possible_actions:
                dx_act, dy_act = my_snake.DIRECTIONS_MAP[action]
                new_pos = ((head_pos[0] + dx_act) % grid_width, (head_pos[1] + dy_act) % grid_height)
                dist = minimal_distance(new_pos, opponent_head)
                if dist > max_dist:
                    max_dist = dist
                    best_evasion_action = action
            return best_evasion_action
        else:
            # Chase strategically
            dx_opponent = (opponent_head[0] - head_pos[0]) % grid_width
            dy_opponent = (opponent_head[1] - head_pos[1]) % grid_height
            preferred = None
            if dx_opponent > dy_opponent:
                preferred = 1 if dx_opponent > 0 else 3
            else:
                preferred = 0 if dy_opponent > 0 else 2
            if preferred in possible_actions:
                return preferred
            # Fallback to minimizing distance
            best_action = None
            min_dist = float('inf')
            for action in possible_actions:
                dx_act, dy_act = my_snake.DIRECTIONS_MAP[action]
                new_pos = ((head_pos[0] + dx_act) % grid_width, (head_pos[1] + dy_act) % grid_height)
                dist = minimal_distance(new_pos, opponent_head)
                if dist < min_dist:
                    min_dist = dist
                    best_action = action
            return best_action

    # Default to random valid action if no other logic applies
    return random.choice(possible_actions)