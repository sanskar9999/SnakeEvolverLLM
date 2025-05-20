import random
from collections import deque

def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    valid_actions = my_snake.get_valid_actions()
    if not valid_actions:
        return my_snake.direction_idx

    head_pos = my_snake.get_head_position()
    opponent_alive = opponent_snake.is_alive if opponent_snake else False

    # Helper function to calculate minimal distance considering grid wrap
    def minimal_distance(pos1, pos2):
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        dx = min(dx, grid_width - dx)
        dy = min(dy, grid_height - dy)
        return dx + dy

    # Check for collisions with self or opponent
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

    # Target food if available and no opponent
    if not opponent_alive and foods:
        food_pos = foods[0].position
        best_action = None
        min_dist = float('inf')
        for action in possible_actions:
            dx, dy = my_snake.DIRECTIONS_MAP[action]
            new_pos = ((head_pos[0] + dx) % grid_width, (head_pos[1] + dy) % grid_height)
            dist = minimal_distance(new_pos, food_pos)
            if dist < min_dist:
                min_dist = dist
                best_action = action
        return best_action

    # Strategic movements based on opponent's state
    if opponent_alive:
        opponent_head = opponent_snake.get_head_position()
        my_length = my_snake.length
        opponent_length = opponent_snake.length

        # Determine relative position considering grid wrap
        dx_opponent = (opponent_head[0] - head_pos[0]) % grid_width
        dy_opponent = (opponent_head[1] - head_pos[1]) % grid_height

        # If longer than opponent, chase aggressively
        if my_length > opponent_length:
            preferred = None
            if dx_opponent > dy_opponent:
                preferred = 1 if dx_opponent > 0 else 3
            else:
                preferred = 0 if dy_opponent > 0 else 2
            if preferred in possible_actions:
                return preferred
            # Calculate action that minimizes distance
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

        # If shorter, prioritize food and evasion
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

        # Same length - focus on control and positioning
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

            # Alternate between chasing and evading based on proximity
            current_dist = minimal_distance(head_pos, opponent_head)
            if current_dist < 5:
                # Evade - maximize distance
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

    # Default to random action if no other logic applies
    return random.choice(possible_actions)