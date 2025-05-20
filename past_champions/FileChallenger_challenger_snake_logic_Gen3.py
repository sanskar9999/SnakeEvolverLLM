# --- START OF FILE challenger_snake_logic.py ---

import random
# from main_snake_game import Snake # For type hinting

# This file will be overwritten by the LLM if --use-llm is active.
# It serves as a fallback or a place for manual challenger logic.
def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    # Default Challenger: Simple food seeking, basic obstacle avoidance
    valid_actions = my_snake.get_valid_actions()
    if not valid_actions: return my_snake.direction_idx 

    head_pos = my_snake.get_head_position()
    
    safe_actions = []
    for act in valid_actions:
        next_dx, next_dy = my_snake.DIRECTIONS_MAP[act]
        next_pos = ((head_pos[0] + next_dx) % grid_width, (head_pos[1] + next_dy) % grid_height)
        
        temp_my_body_for_check = list(my_snake.positions)
        if len(temp_my_body_for_check) >= my_snake.length: # Tail will move
            temp_my_body_for_check = temp_my_body_for_check[:-1]
        
        opponent_full_body = []
        if opponent_snake and opponent_snake.is_alive: # Check if opponent exists and is alive
            opponent_full_body = list(opponent_snake.positions)

        if next_pos not in temp_my_body_for_check and next_pos not in opponent_full_body:
            safe_actions.append(act)
            
    if not safe_actions: # No move is "safe" by this simple check
        return random.choice(valid_actions) if valid_actions else my_snake.direction_idx

    if foods:
        food_pos = foods[0].position
        best_food_action = None
        min_dist_sq = float('inf')

        for act in safe_actions:
            next_dx, next_dy = my_snake.DIRECTIONS_MAP[act]
            next_pos = ((head_pos[0] + next_dx) % grid_width, (head_pos[1] + next_dy) % grid_height)
            
            dx_abs = abs(next_pos[0] - food_pos[0])
            dy_abs = abs(next_pos[1] - food_pos[1])
            # Consider wrap-around for distance calculation
            dist_x_wrapped = min(dx_abs, grid_width - dx_abs)
            dist_y_wrapped = min(dy_abs, grid_height - dy_abs)
            dist_sq = dist_x_wrapped**2 + dist_y_wrapped**2 # Squared Euclidean distance
            
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                best_food_action = act
        
        if best_food_action is not None:
            return best_food_action
            
    return random.choice(safe_actions) # Default to random safe action
