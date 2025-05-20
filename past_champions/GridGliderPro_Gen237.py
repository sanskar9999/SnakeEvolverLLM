import random

def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    valid_actions = my_snake.get_valid_actions()
    if not valid_actions:
        return my_snake.direction_idx
    
    head_pos = my_snake.get_head_position()
    opponent_alive = opponent_snake.is_alive if opponent_snake else False
    
    # Helper function to calculate Manhattan distance
    def manhattan_distance(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    # Helper function to check for collisions
    def is_collision(action):
        dx, dy = my_snake.DIRECTIONS_MAP[action]
        new_x = (head_pos[0] + dx) % grid_width
        new_y = (head_pos[1] + dy) % grid_height
        if (new_x, new_y) in my_snake.positions:
            return True
        if opponent_alive and (new_x, new_y) in opponent_snake.positions:
            return True
        return False
    
    # Filter out actions that cause immediate collisions
    possible_actions = [action for action in valid_actions if not is_collision(action)]
    if not possible_actions:
        return my_snake.direction_idx
    
    # If opponent is dead or not present, focus on food
    if not opponent_alive:
        if foods:
            food_pos = foods[0].position
            # Calculate relative position considering grid wrap
            dx = (food_pos[0] - head_pos[0]) % grid_width
            dy = (food_pos[1] - head_pos[1]) % grid_height
            # Choose direction that gets closer to food
            if dx > dy:
                preferred = 1 if dx > 0 else 3
            else:
                preferred = 0 if dy > 0 else 2
            if preferred in possible_actions:
                return preferred
        # If no food, choose action that maintains direction or random if needed
        return random.choice(possible_actions)
    
    # If opponent is alive, implement strategic movements
    else:
        opponent_head = opponent_snake.get_head_position()
        my_length = my_snake.length
        opponent_length = opponent_snake.length
        
        # Calculate distances
        distance_to_food = manhattan_distance(head_pos, foods[0].position) if foods else float('inf')
        distance_to_opponent = manhattan_distance(head_pos, opponent_head)
        
        # Strategy based on snake length comparison
        if my_length > opponent_length:
            # Chase opponent aggressively
            dx = (opponent_head[0] - head_pos[0]) % grid_width
            dy = (opponent_head[1] - head_pos[1]) % grid_height
            if dx > dy:
                preferred = 1 if dx > 0 else 3
            else:
                preferred = 0 if dy > 0 else 2
            if preferred in possible_actions:
                return preferred
            
            # Choose action that minimizes distance to opponent
            best_action = None
            min_distance = float('inf')
            for action in possible_actions:
                dx_act, dy_act = my_snake.DIRECTIONS_MAP[action]
                new_x = (head_pos[0] + dx_act) % grid_width
                new_y = (head_pos[1] + dy_act) % grid_height
                dist = manhattan_distance((new_x, new_y), opponent_head)
                if dist < min_distance:
                    min_distance = dist
                    best_action = action
            return best_action
        elif my_length < opponent_length:
            # Evade and focus on growing
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
            
            # Choose action that maximizes distance from opponent
            best_action = None
            max_distance = -1
            for action in possible_actions:
                dx_act, dy_act = my_snake.DIRECTIONS_MAP[action]
                new_x = (head_pos[0] + dx_act) % grid_width
                new_y = (head_pos[1] + dy_act) % grid_height
                dist = manhattan_distance((new_x, new_y), opponent_head)
                if dist > max_distance:
                    max_distance = dist
                    best_action = action
            return best_action
        else:
            # Same length - try to outmaneuver
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
            
            # Alternate between chasing and evading based on distance
            if distance_to_opponent < 5:
                # Too close, try to evade
                best_action = None
                max_distance = -1
                for action in possible_actions:
                    dx_act, dy_act = my_snake.DIRECTIONS_MAP[action]
                    new_x = (head_pos[0] + dx_act) % grid_width
                    new_y = (head_pos[1] + dy_act) % grid_height
                    dist = manhattan_distance((new_x, new_y), opponent_head)
                    if dist > max_distance:
                        max_distance = dist
                        best_action = action
                return best_action
            else:
                # Safe to chase
                dx = (opponent_head[0] - head_pos[0]) % grid_width
                dy = (opponent_head[1] - head_pos[1]) % grid_height
                if dx > dy:
                    preferred = 1 if dx > 0 else 3
                else:
                    preferred = 0 if dy > 0 else 2
                if preferred in possible_actions:
                    return preferred
                
                # Fallback to random
                return random.choice(possible_actions)
    
    # Default action
    return my_snake.direction_idx