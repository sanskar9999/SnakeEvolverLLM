# --- START OF FILE main_snake_game.py ---

import os
import random
import time
import shutil
import importlib.util
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable, Dict, Any
import re
import argparse
import json

# Attempt to import Groq
try:
    from groq import Groq
except ImportError:
    Groq = None # Will be checked later

# --- Constants ---
GRID_WIDTH = 20
GRID_HEIGHT = 10
INITIAL_SNAKE_LENGTH = 5
MAX_SNAKE_LENGTH = GRID_WIDTH * GRID_HEIGHT // 2
MAX_STEPS_PER_EPISODE = GRID_WIDTH * GRID_HEIGHT * 2 # Increased steps for longer games

SEED = 42
LEADERBOARD_SIZE = 5
LEADERBOARD_FILE = "leaderboard.json"
PAST_CHAMPIONS_DIR = "past_champions"
DEFAULT_CHALLENGER_NAME = "DefaultChallenger"
MAX_GAUNTLET_OPPONENTS = 3 # Challenger must beat up to this many top snakes


# --- Game Classes ---
@dataclass
class Food:
    position: Tuple[int, int]

class Snake:
    DIRECTIONS_MAP = [(0, -1), (1, 0), (0, 1), (-1, 0)] # UP, RIGHT, DOWN, LEFT
    ACTIONS_LIST = [0, 1, 2, 3]
    OPPOSITE_ACTIONS_MAP = {0: 2, 1: 3, 2: 0, 3: 1}

    def __init__(self, x: int, y: int, initial_direction_idx: Optional[int] = None):
        self.positions = deque() # Initialize empty, then add head first
        self.direction_idx = initial_direction_idx if initial_direction_idx is not None \
                             else random.choice(self.ACTIONS_LIST)
        self.length = INITIAL_SNAKE_LENGTH
        self.score = 0
        self.is_alive = True

        # Initialize head
        head_pos = (x,y)
        self.positions.appendleft(head_pos)
        
        # Initialize body segments based on initial direction
        current_segment_x, current_segment_y = head_pos
        
        # To build the tail, we find positions "behind" the head, moving in the direction opposite to the snake's initial movement.
        # Example: If snake moves RIGHT (dx=1, dy=0), the segment behind the head is to its LEFT (dx=-1, dy=0 from head).
        # So, we use the negative of the direction vector.
        
        # Vector pointing from a body segment to the one in front of it (towards the head)
        # is self.DIRECTIONS_MAP[self.direction_idx]
        # Vector pointing from a body segment to the one behind it (towards the tail)
        # is the negative of that.
        
        dx_segment_growth = -self.DIRECTIONS_MAP[self.direction_idx][0]
        dy_segment_growth = -self.DIRECTIONS_MAP[self.direction_idx][1]

        for _ in range(1, INITIAL_SNAKE_LENGTH):
            next_segment_x = (current_segment_x + dx_segment_growth + GRID_WIDTH) % GRID_WIDTH
            next_segment_y = (current_segment_y + dy_segment_growth + GRID_HEIGHT) % GRID_HEIGHT
            
            # Check for immediate overlap during initialization (highly unlikely for small INITIAL_SNAKE_LENGTH)
            if (next_segment_x, next_segment_y) in self.positions:
                # This would mean the snake is trying to initialize by curling back on itself immediately.
                # For INITIAL_SNAKE_LENGTH <= min(GRID_WIDTH, GRID_HEIGHT), this shouldn't happen.
                # print(f"Warning: Snake body overlap during initialization at ({next_segment_x}, {next_segment_y}). Truncating.")
                break 
            
            self.positions.append((next_segment_x, next_segment_y))
            current_segment_x, current_segment_y = next_segment_x, next_segment_y
        
    def get_head_position(self) -> Tuple[int, int]:
        return self.positions[0]

    def get_current_direction_vector(self) -> Tuple[int, int]:
        return self.DIRECTIONS_MAP[self.direction_idx]

    def get_valid_actions(self) -> List[int]:
        if not self.is_alive: return []
        # Prevent 180-degree turns
        invalid_action = self.OPPOSITE_ACTIONS_MAP[self.direction_idx]
        return [a for a in self.ACTIONS_LIST if a != invalid_action]

    def move(self, action_idx: int) -> bool: # Returns True if snake died from self-collision
        if not self.is_alive: return False

        self.direction_idx = action_idx
        head_x, head_y = self.get_head_position()
        dx, dy = self.get_current_direction_vector()
        new_head = ((head_x + dx) % GRID_WIDTH, (head_y + dy) % GRID_HEIGHT)

        # Check for self-collision (excluding the tail if it's about to move away)
        body_to_check = list(self.positions)
        if len(body_to_check) >= self.length: 
            body_to_check = body_to_check[:-1] 
        
        if new_head in body_to_check:
            self.is_alive = False
            return True 

        self.positions.appendleft(new_head)
        if len(self.positions) > self.length:
            self.positions.pop()
        return False 

    def grow(self):
        if not self.is_alive: return
        self.length = min(self.length + 1, MAX_SNAKE_LENGTH)
        self.score += 1

# --- Helper strings for LLM Prompt ---
SNAKE_CLASS_API_DOCS = f"""
- `positions`: deque of (x, y) tuples. Head is at `my_snake.positions[0]`. Tail is `my_snake.positions[-1]`.
- `direction_idx`: Current direction index (0:Up, 1:Right, 2:Down, 3:Left).
- `length`: Current length of the snake.
- `score`: Food eaten by the snake.
- `is_alive`: Boolean, True if the snake is alive.
- `get_head_position() -> (x, y)`: Returns the (x,y) coordinates of the snake's head.
- `get_valid_actions() -> List[int]`: Returns a list of action indices [0,1,2,3] that are valid (i.e., not an immediate 180-degree turn).
- `DIRECTIONS_MAP`: Class attribute `Snake.DIRECTIONS_MAP` = {Snake.DIRECTIONS_MAP}. Your function will have access to `my_snake.DIRECTIONS_MAP`.
- `ACTIONS_LIST`: Class attribute `Snake.ACTIONS_LIST` = {Snake.ACTIONS_LIST}. Your function will have access to `my_snake.ACTIONS_LIST`.
- `OPPOSITE_ACTIONS_MAP`: Class attribute `Snake.OPPOSITE_ACTIONS_MAP` = {Snake.OPPOSITE_ACTIONS_MAP}. Your function will have access to `my_snake.OPPOSITE_ACTIONS_MAP`.
"""

GAME_CONSTANTS_DOCS = f"""
- GRID_WIDTH: {GRID_WIDTH} (width of the game board)
- GRID_HEIGHT: {GRID_HEIGHT} (height of the game board)
- INITIAL_SNAKE_LENGTH: {INITIAL_SNAKE_LENGTH}
- MAX_SNAKE_LENGTH: {MAX_SNAKE_LENGTH}
- MAX_STEPS_PER_EPISODE: {MAX_STEPS_PER_EPISODE} (game ends if it lasts this long)
"""

# --- Helper: Dynamic Logic Loading ---
def load_logic_from_file(filepath: str, function_name: str) -> Optional[Callable]:
    if not os.path.exists(filepath):
        print(f"Error: Logic file not found: {filepath}")
        return None
    try:
        module_name = f"snake_logic_module_{os.path.basename(filepath).replace('.py', '')}_{function_name}_{random.randint(1000,9999)}"
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec is None or spec.loader is None: 
            print(f"Error: Could not create spec for {filepath}")
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module) 
        return getattr(module, function_name)
    except Exception as e:
        print(f"Error loading logic from {filepath}: {e}")
        return None

# --- Helper: LLM Code and Name Extraction ---
def extract_llm_response_data(llm_response_text: str) -> Optional[Tuple[str, str]]:
    try:
        data = json.loads(llm_response_text)
        name = data.get("challenger_name")
        code = data.get("python_code")
        if name and code:
            print(f"Successfully parsed JSON: Challenger Name '{name}'")
            return str(name), str(code)
        print("Warning: Parsed JSON but 'challenger_name' or 'python_code' missing.")
    except json.JSONDecodeError:
        print("Warning: LLM response was not valid JSON. Falling back to code block extraction.")

    code_match = re.search(r"```python\s*([\s\S]+?)\s*```", llm_response_text)
    if not code_match: 
        code_match = re.search(r"```\s*([\s\S]+?)\s*```", llm_response_text)
    
    if code_match:
        code = code_match.group(1).strip()
        name_match = re.search(r"^\s*CHALLENGER_NAME\s*:\s*(.+)$", llm_response_text, re.MULTILINE | re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else f"LLM_Challenger_Gen{current_generation}"
        print(f"Warning: Using fallback code extraction. Deduced Name: '{name}'")
        return name, code

    if "def get_challenger_action" in llm_response_text: 
        lines = llm_response_text.strip().split('\n')
        if lines and (lines[0].lower().startswith("import ") or lines[0].lower().startswith("def ") or lines[0].startswith("#")): 
            if "return" in llm_response_text: 
                name = f"LLM_Challenger_Gen{current_generation}_Fallback"
                print(f"Warning: No code markers or JSON. Using full response as code. Deduced Name: '{name}'.")
                return name, llm_response_text.strip()
    
    print("Error: Could not extract Python code or name from LLM response.")
    print("LLM Response was:\n", llm_response_text[:1000] + "..." if len(llm_response_text) > 1000 else llm_response_text)
    return None

# --- LLM Code Generation Function (Now using Groq) ---
def generate_challenger_code_with_llm(api_key: str, current_best_code: str, snake_api_docs: str, game_constants_docs: str, generation: int) -> Optional[Tuple[str, str]]:
    if not Groq:
        print("Error: groq library is not installed. Cannot generate code with LLM.")
        print("Please install it: pip install groq")
        return None

    print(f"\n--- Attempting to generate Challenger Snake Logic (Generation {generation}) with Groq LLM ---")
    
    model_name = "llama-3.1-8b-instant" # Using a generally available powerful model on Groq. User's prompt had "qwen-qwq-32b" which might be specific.

    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return None

    full_prompt = f"""
You are an expert Python programmer developing an AI for a 1v1 Snake game.
Your goal is to write the logic for a new challenger snake. If your snake performs well against the current champion(s), its code will become the new champion.

You need to implement the Python function `get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height)`.

Game Constants:
{game_constants_docs}

`my_snake` (Your Snake object) and `opponent_snake` (Opponent's Snake object) API:
{snake_api_docs}
Note: `opponent_snake` might be None or `opponent_snake.is_alive` might be False. Always check.

`foods`: A list of Food objects. `foods[0].position` is the (x, y) location. Check `if foods:`.
The grid wraps around (toroidal world). (0,0) is top-left.

Objectives (in order):
1.  Survival: Avoid self-collision and opponent collision.
2.  Eat Food: Grow longer.
3.  Outmaneuver Opponent: Aggressive (trapping) or defensive strategies. Longer snakes win head-on. Equal length head-on means both die.

The current champion snake's logic (whose code is in `best_snake_logic.py` and you must try to defeat) is:
```python
{current_best_code}
```
You will be playing against a gauntlet of top snakes. Your goal is to beat them all.

IMPORTANT INSTRUCTIONS FOR YOUR RESPONSE:
1.  Your response MUST be a single JSON object.
2.  The JSON object must have two keys:
    *   `"challenger_name"`: A string with a creative and unique name for your snake logic (e.g., "SerpentineStrategist", "GridGliderPro").
    *   `"python_code"`: A string containing the complete Python code for the `get_challenger_action` function, including any necessary standard library imports (e.g., `import random`).

Example JSON response format:
```json
{{
  "challenger_name": "ByteViper X",
  "python_code": "import random\\n# from main_snake_game import Snake # Optional type hint\\n\\ndef get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):\\n    # ... your brilliant logic ...\\n    valid_actions = my_snake.get_valid_actions()\\n    if not valid_actions: return my_snake.direction_idx\\n    chosen_action = random.choice(valid_actions)\\n    return chosen_action"
}}
```
- Ensure the `python_code` string is properly escaped if it contains newlines or special characters for JSON.
- The function signature in your code MUST be `def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):`.
- Return one of the action indices: 0 (Up), 1 (Right), 2 (Down), or 3 (Left).
- Strive to return a valid action from `my_snake.get_valid_actions()`.
"""
    messages = [{"role": "user", "content": full_prompt}]

    print(f"Sending prompt to Groq LLM (model: {model_name})...")
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.8, # Slightly higher for more creativity
            max_tokens=131072,
            top_p=0.9,
            stream=False,
            response_format={"type": "json_object"}
        )
        
        if completion.choices and completion.choices[0].message and completion.choices[0].message.content:
            llm_response_text = completion.choices[0].message.content
            print("Groq LLM response received.")
            return extract_llm_response_data(llm_response_text)
        else:
            print("Error: Groq LLM response did not contain expected content.")
            if completion.usage: print(f"Usage: {completion.usage}")
            return None

    except Exception as e:
        print(f"Error during Groq LLM call: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_details = e.response.json()
                print(f"Groq API Error Details: {error_details}")
            except:
                print(f"Groq API Error Response (text): {e.response.text}")
        return None

class SnakeEnvironment:
    def __init__(self):
        self.snake1: Optional[Snake] = None
        self.snake2: Optional[Snake] = None
        self.foods: List[Food] = []
        self.game_over = False
        self.steps_taken = 0

    def reset(self):
        self.steps_taken = 0
        self.game_over = False
        
        while True:
            pos1 = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            dir1_idx = random.choice(Snake.ACTIONS_LIST)
            self.snake1 = Snake(*pos1, initial_direction_idx=dir1_idx)

            pos2 = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            while any(p in self.snake1.positions for p in Snake(*pos2, initial_direction_idx=random.choice(Snake.ACTIONS_LIST)).positions): # Check full initial body
                 pos2 = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            
            dir2_idx = random.choice(Snake.ACTIONS_LIST)
            temp_snake2_for_check = Snake(*pos2, initial_direction_idx=dir2_idx)

            if pos1 == pos2 and dir1_idx == Snake.OPPOSITE_ACTIONS_MAP[dir2_idx]:
                 valid_dirs = [d for d in Snake.ACTIONS_LIST if d != Snake.OPPOSITE_ACTIONS_MAP[dir1_idx]]
                 dir2_idx = random.choice(valid_dirs) if valid_dirs else dir2_idx 
                 temp_snake2_for_check = Snake(*pos2, initial_direction_idx=dir2_idx)


            if not any(p2_seg in self.snake1.positions for p2_seg in temp_snake2_for_check.positions):
                 self.snake2 = temp_snake2_for_check # Assign the validated snake
                 break 

        self.foods = []
        self._spawn_food()
        return self.snake1, self.snake2, self.foods

    def _spawn_food(self):
        if len(self.foods) > 0: return 
        occupied_cells = set()
        if self.snake1 and self.snake1.is_alive: occupied_cells.update(self.snake1.positions)
        if self.snake2 and self.snake2.is_alive: occupied_cells.update(self.snake2.positions)
        
        empty_cells = [(x, y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT) if (x,y) not in occupied_cells]
        if empty_cells:
            self.foods.append(Food(random.choice(empty_cells)))

    def step(self, action1: int, action2: int) -> Tuple[bool, bool, bool]: 
        if self.game_over:
            return True, not (self.snake1 and self.snake1.is_alive), not (self.snake2 and self.snake2.is_alive)

        self.steps_taken += 1
        s1_died_self, s2_died_self = False, False

        if self.snake1 and self.snake1.is_alive: s1_died_self = self.snake1.move(action1)
        if self.snake2 and self.snake2.is_alive: s2_died_self = self.snake2.move(action2)

        s1_killed_by_s2, s2_killed_by_s1 = False, False

        if self.snake1 and self.snake1.is_alive and self.snake2 and self.snake2.is_alive:
            head1, head2 = self.snake1.get_head_position(), self.snake2.get_head_position()
            if head1 == head2: 
                if self.snake1.length > self.snake2.length: s2_killed_by_s1 = True; self.snake2.is_alive = False
                elif self.snake2.length > self.snake1.length: s1_killed_by_s2 = True; self.snake1.is_alive = False
                else: 
                    s1_killed_by_s2 = True; self.snake1.is_alive = False
                    s2_killed_by_s1 = True; self.snake2.is_alive = False
            else:
                if head1 in list(self.snake2.positions)[1:]: 
                    s1_killed_by_s2 = True; self.snake1.is_alive = False
                if self.snake2.is_alive and head2 in list(self.snake1.positions)[1:]:
                    s2_killed_by_s1 = True; self.snake2.is_alive = False
        
        snake1_killed_this_step = s1_died_self or s1_killed_by_s2
        snake2_killed_this_step = s2_died_self or s2_killed_by_s1
        
        if self.foods:
            food_pos = self.foods[0].position
            ate_food = False
            if self.snake1 and self.snake1.is_alive and self.snake1.get_head_position() == food_pos:
                self.snake1.grow(); ate_food = True
            elif self.snake2 and self.snake2.is_alive and self.snake2.get_head_position() == food_pos:
                self.snake2.grow(); ate_food = True
            
            if ate_food:
                self.foods.pop(0)
                self._spawn_food()

        s1_truly_alive = self.snake1 and self.snake1.is_alive
        s2_truly_alive = self.snake2 and self.snake2.is_alive
        if not s1_truly_alive or not s2_truly_alive or self.steps_taken >= MAX_STEPS_PER_EPISODE:
            self.game_over = True
        
        return self.game_over, snake1_killed_this_step, snake2_killed_this_step

# --- Rendering ---
def render_game(env: SnakeEnvironment, challenger_name: str, opponent_name: str):
    grid = [['.' for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    if env.foods: grid[env.foods[0].position[1]][env.foods[0].position[0]] = 'F' 

    if env.snake2: 
        char_head, char_body, char_dead = 'O', 'x', 'X' # Opponent: Head, body, dead_head
        if env.snake2.is_alive:
            for i, pos in enumerate(list(env.snake2.positions)): grid[pos[1]][pos[0]] = char_head if i == 0 else char_body
        elif env.snake2.positions: 
            grid[env.snake2.get_head_position()[1]][env.snake2.get_head_position()[0]] = char_dead

    if env.snake1: 
        char_head, char_body, char_dead = 'C', 'o', 'X' # Challenger: Head, body, dead_head
        if env.snake1.is_alive:
            for i, pos in enumerate(list(env.snake1.positions)): grid[pos[1]][pos[0]] = char_head if i == 0 else char_body
        elif env.snake1.positions: 
            grid[env.snake1.get_head_position()[1]][env.snake1.get_head_position()[0]] = char_dead
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"Generation: {current_generation} | Step: {env.steps_taken}/{MAX_STEPS_PER_EPISODE}")
    s1_score = env.snake1.score if env.snake1 else 'N/A'
    s2_score = env.snake2.score if env.snake2 else 'N/A'
    s1_status = "Alive" if env.snake1 and env.snake1.is_alive else "Dead"
    s2_status = "Alive" if env.snake2 and env.snake2.is_alive else "Dead"

    print(f"S1 (Challenger: {challenger_name}): Food {s1_score} ({s1_status}) | S2 (Opponent: {opponent_name}): Food {s2_score} ({s2_status})")
    print('+' + '-' * GRID_WIDTH + '+')
    for row_idx in range(GRID_HEIGHT): print('|' + ''.join(grid[row_idx]) + '|')
    print('+' + '-' * GRID_WIDTH + '+')

# --- Leaderboard Management ---
leaderboard: List[Dict[str, Any]] = []
current_generation: int = 0 

def load_leaderboard():
    global leaderboard
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                leaderboard = json.load(f)
            print(f"Loaded leaderboard from {LEADERBOARD_FILE}")
        except Exception as e:
            print(f"Error loading leaderboard: {e}. Starting fresh.")
            leaderboard = []
    else:
        leaderboard = []

def save_leaderboard():
    try:
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(leaderboard, f, indent=2)
        print(f"Saved leaderboard to {LEADERBOARD_FILE}")
    except Exception as e:
        print(f"Error saving leaderboard: {e}")

def update_and_display_leaderboard(new_champion_name: str, generation_crowned: int, champion_code_file_basename: str):
    global leaderboard
    print(f"\n--- NEW OVERALL CHAMPION: {new_champion_name} (Crowned at Gen {generation_crowned}) ---")
    
    leaderboard = [entry for entry in leaderboard if entry["name"] != new_champion_name]
    
    leaderboard.append({
        "name": new_champion_name,
        "generation_crowned": generation_crowned,
        "file": champion_code_file_basename 
    })
    
    leaderboard.sort(key=lambda x: (-x["generation_crowned"], x["name"]))
    leaderboard = leaderboard[:LEADERBOARD_SIZE] 
    
    print("\n--- Top Snakes Leaderboard ---")
    if not leaderboard:
        print("Leaderboard is empty.")
    else:
        for i, entry in enumerate(leaderboard):
            print(f"{i+1}. {entry['name']} (Crowned Gen: {entry['generation_crowned']}, File: {entry['file']})")
    print("-----------------------------\n")
    save_leaderboard()

# --- Gauntlet Opponent Selection ---
def get_gauntlet_opponents(leaderboard_list: List[Dict[str, Any]],
                           current_best_overall_logic_file: str, 
                           name_for_current_best_file_logic: str,
                           past_champions_dir: str,
                           max_opponents: int) -> List[Tuple[str, str]]: # (name, filepath)
    
    gauntlet_opponents_to_face = []
    
    # Add from leaderboard first
    for i in range(min(len(leaderboard_list), max_opponents)):
        entry = leaderboard_list[i]
        opponent_name = entry["name"]
        opponent_file_path = os.path.join(past_champions_dir, entry["file"])
        if os.path.exists(opponent_file_path):
            gauntlet_opponents_to_face.append((opponent_name, opponent_file_path))
        else:
            print(f"Warning: Leaderboard champion file '{opponent_file_path}' for '{opponent_name}' not found. Skipping.")

    # If gauntlet is empty (e.g., fresh leaderboard or all files missing)
    # the challenger faces the logic in current_best_overall_logic_file.
    if not gauntlet_opponents_to_face:
        if os.path.exists(current_best_overall_logic_file):
            print(f"Leaderboard empty or top files missing. Challenger faces current logic in '{current_best_overall_logic_file}'.")
            gauntlet_opponents_to_face.append((name_for_current_best_file_logic, current_best_overall_logic_file))
        else:
            # This is a critical state: no leaderboard and no fallback best file.
            print(f"CRITICAL: No leaderboard opponents and '{current_best_overall_logic_file}' not found. Cannot set up gauntlet.")
            return [] # No one to play against

    if not gauntlet_opponents_to_face: # Should be caught by CRITICAL print, but safeguard
        return []

    print(f"\nChallenger Gauntlet (must win match series against all {len(gauntlet_opponents_to_face)}):")
    for i, (name, path) in enumerate(gauntlet_opponents_to_face):
        is_primary_target = (i == 0) # The first in this list is the highest-ranked opponent
        target_tag = " (Primary Target)" if is_primary_target else ""
        print(f"  {i+1}. {name}{target_tag} (from {path})")
    
    return gauntlet_opponents_to_face


# --- Competition Runner ---
def run_match_series(challenger_logic_file: str, opponent_logic_file: str, 
                     challenger_name_str: str, opponent_name_str: str,
                     num_games: int, render_flag: bool) -> bool: # Returns True if challenger wins majority
    
    challenger_logic = load_logic_from_file(challenger_logic_file, "get_challenger_action")
    opponent_logic = load_logic_from_file(opponent_logic_file, "get_challenger_action")

    if not challenger_logic:
        print(f"CRITICAL Error: Failed to load challenger snake logic from {challenger_logic_file}. Challenger forfeits this match series.")
        return False 
    if not opponent_logic:
        print(f"Warning: Failed to load opponent snake logic from {opponent_logic_file}. Using dummy random for opponent '{opponent_name_str}'.")
        def dummy_logic(my_snake, opponent_snake, foods, grid_width, grid_height):
            valid_actions = my_snake.get_valid_actions()
            return random.choice(valid_actions) if valid_actions else my_snake.direction_idx
        opponent_logic = dummy_logic
        opponent_name_str = f"{opponent_name_str}_DummyFallback"


    env = SnakeEnvironment()
    challenger_match_score = 0 # Tracks game outcomes: +1 for challenger win, -1 for opponent win, 0 for tie

    print(f"\n--- Starting Match Series: {challenger_name_str} (Challenger) vs. {opponent_name_str} (Opponent) ({num_games} games) ---")

    for game_num in range(1, num_games + 1):
        snake1, snake2, foods = env.reset() # snake1 is challenger, snake2 is opponent
        game_over = False
        
        if render_flag:
            render_game(env, challenger_name_str, opponent_name_str)
            time.sleep(0.1) 

        while not game_over:
            action1, action2 = snake1.direction_idx, snake2.direction_idx 

            if snake1.is_alive:
                valid_actions1 = snake1.get_valid_actions()
                if valid_actions1:
                    try:
                        action1 = challenger_logic(snake1, snake2, foods, GRID_WIDTH, GRID_HEIGHT)
                        if action1 not in valid_actions1: 
                            action1 = random.choice(valid_actions1)
                    except Exception:
                        action1 = random.choice(valid_actions1)
                else: 
                    action1 = snake1.direction_idx 
            
            if snake2.is_alive:
                valid_actions2 = snake2.get_valid_actions()
                if valid_actions2:
                    try:
                        action2 = opponent_logic(snake2, snake1, foods, GRID_WIDTH, GRID_HEIGHT)
                        if action2 not in valid_actions2: 
                            action2 = random.choice(valid_actions2)
                    except Exception:
                        action2 = random.choice(valid_actions2)
                else:
                    action2 = snake2.direction_idx

            game_over, _, _ = env.step(action1, action2)
            foods = env.foods 

            if render_flag:
                render_game(env, challenger_name_str, opponent_name_str)
                time.sleep(0.05 if num_games <= 20 else 0.001) 
            
            if game_over: break
        
        game_result_for_challenger = 0
        s1_alive, s2_alive = (snake1 and snake1.is_alive), (snake2 and snake2.is_alive)

        if not s1_alive and not s2_alive: 
            if snake1.score > snake2.score: game_result_for_challenger = 1
            elif snake2.score > snake1.score: game_result_for_challenger = -1
        elif not s1_alive: game_result_for_challenger = -1 
        elif not s2_alive: game_result_for_challenger = 1  
        else: 
            if snake1.score > snake2.score: game_result_for_challenger = 1
            elif snake2.score > snake1.score: game_result_for_challenger = -1
            elif snake1.length > snake2.length: game_result_for_challenger = 1 
            elif snake2.length > snake1.length: game_result_for_challenger = -1
        
        challenger_match_score += game_result_for_challenger
        if render_flag and game_num < num_games : time.sleep(0.1) 

    print(f"\n--- Match Series Summary ({challenger_name_str} vs. {opponent_name_str}) ---")
    print(f"Challenger ({challenger_name_str}) Total Score: {challenger_match_score} over {num_games} games.")

    challenger_won_series = challenger_match_score > 0
    if challenger_won_series:
        print(f"Challenger ({challenger_name_str}) WON the series against {opponent_name_str}.")
    elif challenger_match_score == 0:
        print(f"TIED SERIES between {challenger_name_str} and {opponent_name_str}.")
    else:
        print(f"Challenger ({challenger_name_str}) LOST the series against {opponent_name_str}.")
    print("--------------------------------------")
    return challenger_won_series


# --- Main Execution ---
if __name__ == "__main__":
    random.seed(SEED) 

    parser = argparse.ArgumentParser(description="Self-Improving Snake AI Competition with LLM")
    parser.add_argument('--challenger_file', type=str, default='challenger_snake_logic.py', help='Path to the challenger snake logic file.')
    parser.add_argument('--best_file', type=str, default='best_snake_logic.py', help='Path to the current best overall snake logic file (used as fallback or initial champion).')
    parser.add_argument('--games_per_match', type=int, default=10, help='Number of games per match series in the gauntlet.')
    parser.add_argument('--render', action='store_true', help='Render games visually.')
    parser.add_argument('--use-llm', action='store_true', help='Generate challenger logic using an LLM.')
    parser.add_argument('--llm-api-key', type=str, default=os.environ.get("GROQ_API_KEY"), help='API key for Groq. Defaults to GROQ_API_KEY env var.')
    
    args = parser.parse_args()

    if not os.path.exists(PAST_CHAMPIONS_DIR):
        os.makedirs(PAST_CHAMPIONS_DIR)
        print(f"Created directory: {PAST_CHAMPIONS_DIR}")

    load_leaderboard() 
    if leaderboard:
        current_generation = max(entry.get("generation_crowned", 0) for entry in leaderboard) + 1
    else:
        current_generation = 1 

    if not os.path.exists(args.challenger_file):
        print(f"Challenger file '{args.challenger_file}' not found. Creating a default placeholder.")
        default_challenger_code = """import random
def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    valid_actions = my_snake.get_valid_actions()
    if not valid_actions: return my_snake.direction_idx
    return random.choice(valid_actions)
"""
        with open(args.challenger_file, 'w') as f: f.write(default_challenger_code)

    if not os.path.exists(args.best_file):
        print(f"Best overall snake file '{args.best_file}' not found. Creating a default.")
        default_best_code = """import random
# Default Best Snake Logic
def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    # Simple logic: try to go for food, else move randomly
    valid_actions = my_snake.get_valid_actions()
    if not valid_actions: return my_snake.direction_idx

    if foods:
        food_pos = foods[0].position
        head_pos = my_snake.get_head_position()
        
        # Try to move towards food
        # This is a very basic heuristic and can be improved
        best_action = -1
        min_dist_sq = float('inf')

        for action in valid_actions:
            dx, dy = my_snake.DIRECTIONS_MAP[action]
            next_x = (head_pos[0] + dx + grid_width) % grid_width
            next_y = (head_pos[1] + dy + grid_height) % grid_height
            
            dist_sq = (next_x - food_pos[0])**2 + (next_y - food_pos[1])**2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                best_action = action
        
        if best_action != -1:
            return best_action

    return random.choice(valid_actions)
"""
        with open(args.best_file, 'w') as f: f.write(default_best_code)


    while True:
        print(f"\n\n=== STARTING GENERATION {current_generation} ===")
        
        name_for_current_best_file_logic: str
        if leaderboard:
            name_for_current_best_file_logic = leaderboard[0]["name"] # Assumes args.best_file has this logic
        else:
            base_best_filename = os.path.basename(args.best_file).replace('.py','')
            name_for_current_best_file_logic = f"InitialChampion_{base_best_filename}"
            if not os.path.exists(args.best_file): 
                 name_for_current_best_file_logic = "DefaultPlaceholderChampion"

        current_challenger_name = DEFAULT_CHALLENGER_NAME 
        llm_generated_new_code_successfully = False

        if args.use_llm:
            print(f"\n--- Generation {current_generation}: Attempting LLM code generation (Groq) ---")
            api_key_to_use = args.llm_api_key
            can_attempt_llm = True

            if not api_key_to_use:
                print("WARNING: Groq API key not provided. LLM generation SKIPPED.")
                can_attempt_llm = False
            elif not Groq: 
                print("CRITICAL: 'groq' library not installed. LLM generation SKIPPED.")
                can_attempt_llm = False

            if can_attempt_llm:
                try:
                    with open(args.best_file, 'r') as f: # Provide current best overall code as context
                        current_best_code_content = f.read()
                except FileNotFoundError:
                    print(f"Error: Could not read best snake logic file '{args.best_file}' for LLM. Using fallback content.")
                    current_best_code_content = "# Best code not found. Implement basic survival."

                llm_response_tuple = generate_challenger_code_with_llm(
                    api_key_to_use,
                    current_best_code_content,
                    SNAKE_CLASS_API_DOCS,
                    GAME_CONSTANTS_DOCS,
                    current_generation 
                )

                if llm_response_tuple:
                    challenger_name_from_llm, generated_code = llm_response_tuple
                    current_challenger_name = challenger_name_from_llm 
                    print(f"Groq LLM proposed challenger: '{current_challenger_name}'. Writing code to '{args.challenger_file}'.")
                    try:
                        with open(args.challenger_file, 'w') as f: f.write(generated_code)
                        print(f"Successfully wrote Groq LLM-generated code to {args.challenger_file}")
                        llm_generated_new_code_successfully = True
                    except IOError as e:
                        print(f"ERROR: Could not write Groq LLM code to {args.challenger_file}: {e}")
                else:
                    print(f"Groq LLM code generation or extraction failed for Generation {current_generation}.")
            
            if not llm_generated_new_code_successfully:
                print(f"Using existing/default challenger code from '{args.challenger_file}' for Generation {current_generation}.")
                base_challenger_filename = os.path.basename(args.challenger_file).replace('.py','')
                current_challenger_name = f"FileChallenger_{base_challenger_filename}_Gen{current_generation}"
        
        else: 
            base_challenger_filename = os.path.basename(args.challenger_file).replace('.py','')
            current_challenger_name = f"ManualChallenger_{base_challenger_filename}_Gen{current_generation}"
            print(f"LLM not enabled. Using manual challenger: '{current_challenger_name}' from '{args.challenger_file}'.")

        # --- Gauntlet Challenge ---
        print(f"\n--- Generation {current_generation}: Preparing Gauntlet Challenge for '{current_challenger_name}' ---")
        
        gauntlet_opponents = get_gauntlet_opponents(
            leaderboard,
            args.best_file, # Path to the logic of the current #1 or initial champion
            name_for_current_best_file_logic, # Name for the logic in args.best_file
            PAST_CHAMPIONS_DIR,
            MAX_GAUNTLET_OPPONENTS
        )

        if not gauntlet_opponents:
            print("No opponents for gauntlet. Skipping generation. Check configuration and file paths.")
            time.sleep(0.1)
            current_generation +=1 
            continue

        challenger_won_all_gauntlet_matches = True
        if not gauntlet_opponents: # Should be caught above, but for safety
            challenger_won_all_gauntlet_matches = False # Cannot win if no opponents

        for opp_idx, (opponent_name, opponent_logic_file) in enumerate(gauntlet_opponents):
            print(f"\n>>> Gauntlet Match {opp_idx+1}/{len(gauntlet_opponents)}: Challenger '{current_challenger_name}' vs. Opponent '{opponent_name}' <<<")
            
            match_series_won_by_challenger = run_match_series(
                args.challenger_file,
                opponent_logic_file, 
                current_challenger_name,
                opponent_name, 
                args.games_per_match, 
                args.render
            )
            if not match_series_won_by_challenger:
                challenger_won_all_gauntlet_matches = False
                print(f"Challenger '{current_challenger_name}' FAILED against '{opponent_name}'. Gauntlet challenge unsuccessful.")
                break 
            else:
                print(f"Challenger '{current_challenger_name}' SUCCEEDED against '{opponent_name}'.")


        if challenger_won_all_gauntlet_matches:
            print(f"\n!!! CONGRATULATIONS !!!")
            print(f"Challenger '{current_challenger_name}' SUCCESSFULLY BEAT ALL {len(gauntlet_opponents)} OPPONENTS IN THE GAUNTLET!")
            print(f"'{current_challenger_name}' is the new OVERALL CHAMPION of Generation {current_generation}!")
            
            safe_challenger_name = re.sub(r'[^\w_.)( -]', '', current_challenger_name).strip().replace(' ', '_')
            if not safe_challenger_name: 
                safe_challenger_name = f"UnnamedChampion_Gen{current_generation}"
            
            archived_champion_filename_basename = f"{safe_challenger_name}_Gen{current_generation}.py"
            archived_champion_filepath = os.path.join(PAST_CHAMPIONS_DIR, archived_champion_filename_basename)
            
            try:
                shutil.copyfile(args.challenger_file, archived_champion_filepath)
                print(f"Archived new champion's code to: {archived_champion_filepath}")
            except Exception as e:
                print(f"Error archiving champion code: {e}")
                archived_champion_filename_basename = os.path.basename(args.challenger_file) # Fallback

            try:
                shutil.copyfile(args.challenger_file, args.best_file)
                print(f"Updated '{args.best_file}' with new champion logic from '{args.challenger_file}'.")
            except Exception as e:
                print(f"CRITICAL Error updating best snake logic file '{args.best_file}': {e}. Champion update failed.")

            update_and_display_leaderboard(current_challenger_name, current_generation, archived_champion_filename_basename)
        else:
            print(f"\nChallenger '{current_challenger_name}' did not successfully complete the gauntlet in Generation {current_generation}.")
            if gauntlet_opponents: # Only print if there were opponents
                 print(f"The champion(s) remain: {', '.join([opp[0] for opp in gauntlet_opponents]) if leaderboard else name_for_current_best_file_logic}")


        current_generation += 1
        print(f"Pausing briefly before starting Generation {current_generation}...")
        time.sleep(0.1)