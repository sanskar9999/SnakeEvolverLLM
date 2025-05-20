import random
from collections import deque

def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    valid_actions = my_snake.get_valid_actions()
    if not valid_actions:
        return my_snake.direction_idx

    head_pos = my_snake.get_head_position()
    
    # Define possible moves
    possible_moves = []
    for action in valid_actions:
        dx, dy = my_snake.DIRECTIONS_MAP[action]
        next_pos = ((head_pos[0] + dx) % grid_width, (head_pos[1] + dy) % grid_height)
        possible_moves.append((next_pos, action))

    # Check for immediate collisions
    safe_moves = []
    for pos, action in possible_moves:
        # Check self-collision
        if pos in my_snake.positions:
            continue
        
        # Check opponent collision
        if opponent_snake and opponent_snake.is_alive and pos in opponent_snake.positions:
            continue
        
        safe_moves.append(action)

    if not safe_moves:
        return random.choice(valid_actions)

    # Find path to food using A*
    if foods:
        food_pos = foods[0].position
        
        # A* algorithm setup
        open_list = deque()
        closed_list = set()
        
        # Start node
        start_node = (head_pos[0], head_pos[1], my_snake.direction_idx)
        open_list.append((start_node, 0))
        came_from = {} 
        g_score = {start_node: 0}
        f_score = {start_node: heuristic(start_node, food_pos)}

        while open_list:
            current_node, _ = min(open_list, key=lambda x: x[1])
            open_list.popleft()
            
            if current_node == (food_pos[0], food_pos[1], None):
                # Reconstruct path
                path = []
                while current_node in came_from:
                    path.append(current_node)
                    current_node = came_from[current_node]
                
                # Find the first action in path
                for node in path:
                    x, y, action = node
                    if action in safe_moves:
                        return action
                
            closed_list.add(current_node)
            
            # Generate neighbors
            for action in valid_actions:
                dx, dy = my_snake.DIRECTIONS_MAP[action]
                new_x = (current_node[0] + dx) % grid_width
                new_y = (current_node[1] + dy) % grid_height
                
                # Check if new position is safe
                if (new_x, new_y) in my_snake.positions:
                    continue
                if opponent_snake and opponent_snake.is_alive and (new_x, new_y) in opponent_snake.positions:
                    continue
                
                neighbor_node = (new_x, new_y, action)
                if neighbor_node in closed_list:
                    continue
                
                # Calculate scores
                tentative_g_score = g_score[current_node] + 1
                if neighbor_node not in g_score or tentative_g_score < g_score[neighbor_node]:
                    came_from[neighbor_node] = current_node
                    g_score[neighbor_node] = tentative_g_score
                    f_score[neighbor_node] = tentative_g_score + heuristic(neighbor_node, food_pos)
                    open_list.append((neighbor_node, f_score[neighbor_node]))
                    
        # If no path found, choose safest move
    # Default to random safe action
    return random.choice(safe_moves)


def heuristic(node, food_pos):
    x, y, _ = node
    dx = abs(x - food_pos[0])
    dy = abs(y - food_pos[1])
    return dx + dy