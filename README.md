# Snake AI: King of the Hill

Evolve and battle Snake AIs in this "King of the Hill" platform. Features a web viewer (Pyodide) for AI tournaments and a local Python framework with LLM (Groq) powered challenger generation.

https://www.youtube.com/watch?v=eHycx1uYF8c
 
## Overview

This project provides a "King of the Hill" style competition framework for Snake game AIs. It consists of two main parts:

1.  A **web-based viewer (`index.html`)** that uses Pyodide to run Python Snake AIs directly in your browser, allowing you to watch tournaments unfold.
2.  A **local Python script (`main_snake_game.py`)** for running more intensive AI tournaments, managing a leaderboard, and even generating new AI challengers using Large Language Models (LLMs) via the Groq API.

The core idea is that AIs compete to become the "King." New challengers must defeat the current King (or a gauntlet of top AIs in the local version) to take the crown.

## Features

### Web-Based Viewer (`index.html`)
*   Play Snake AI tournaments directly in your browser.
*   Powered by Pyodide, running Python game logic and AIs client-side.
*   Visual game rendering on HTML Canvas.
*   Loads AI agents from a `past_champions/champions_manifest.json` file.
*   Simple controls to start tournaments and progress battles.
*   Displays current King, scores, and AI names.

### Local AI Competition Framework (`main_snake_game.py`)
*   Run "King of the Hill" tournaments locally via the command line.
*   **LLM-Powered Challenger Generation:**
    *   Integrates with the Groq API to generate Python code for new Snake AIs.
    *   Provides the LLM with game rules, API documentation, and the current champion's code as context for improvement.
*   **Gauntlet Mode:** Challengers must win a match series against a gauntlet of top-ranked AIs to become the new champion.
*   Persistent leaderboard (`leaderboard.json`) tracking top-performing AIs.
*   Archives champion AI code in the `past_champions/` directory.
*   Configurable game parameters (grid size, game speed, matches per series).
*   Optional terminal-based rendering of games.

## How it Works

### Web Version (`index.html`)
*   `index.html` sets up the game canvas and UI.
*   It initializes Pyodide to run the Python game engine (code embedded within `index.html`).
*   AIs are defined in Python files (e.g., `my_awesome_ai.py`) and listed in `past_champions/champions_manifest.json`.
*   The browser fetches and loads these AI files using Pyodide.
*   The Python `SnakeEnvironment` class manages the game state, and AI functions are called each step.
*   The game state is rendered on the HTML canvas.

### Local Version (`main_snake_game.py`)
*   The script manages generations of AI competition.
*   In each generation, a challenger AI (either from `challenger_snake_logic.py` or LLM-generated) attempts to defeat a gauntlet of current top AIs (from the `leaderboard.json` and `best_snake_logic.py`).
*   If the challenger succeeds, its code is promoted to `best_snake_logic.py`, archived with a descriptive name in `past_champions/`, and its achievement is recorded on the `leaderboard.json`.
*   When `--use-llm` is active, the script prompts an LLM (via Groq) to write a new `get_challenger_action` function, aiming to beat the current best AI.

## Getting Started / Usage

### Web Version (`index.html`)

1.  **Prerequisites:**
    *   A modern web browser.
    *   To serve `index.html` and associated AI files, you'll need a local web server.
        *   A simple way is to use Python's built-in server: Navigate to the project's root directory in your terminal and run `python -m http.server 8000` (or `python3 -m http.server 8000`).
        *   Then open `http://localhost:8000/index.html` in your browser.

2.  **Setup AI Champions:**
    *   Place your Snake AI Python files (e.g., `ai_agent_1.py`, `ai_agent_2.py`) into the `past_champions/` directory. Each file should contain a function `get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height)`.
    *   Create/update the `past_champions/champions_manifest.json` file to list your AIs:
        ```json
        [
          { "name": "SmartSnake", "file": "smart_snake.py" },
          { "name": "SpeedyViper", "file": "speedy_viper.py" },
          { "name": "CautiousCobra", "file": "cautious_cobra.py" }
        ]
        ```
        The `file` attribute should be the filename of the AI Python script located in the `past_champions/` directory.

3.  **Run:**
    *   Open `index.html` via your local web server.
    *   Click "Start New Tournament" to begin. The first battle will be between two randomly selected AIs from your manifest.
    *   After a game finishes, click "Next Battle". The winner becomes the new King (or retains Kingship) and faces a new random challenger.

### Local Version (`main_snake_game.py`)

1.  **Prerequisites:**
    *   Python 3.x.
    *   (Optional, for LLM generation) `groq` library: `pip install groq`.
    *   (Optional, for LLM generation) A Groq API key. You can set it as an environment variable `GROQ_API_KEY` or pass it via the `--llm-api-key` argument.

2.  **Core Files:**
    *   `main_snake_game.py`: The main script to run tournaments.
    *   `challenger_snake_logic.py`: Place your new/experimental AI logic here. This file is used if LLM generation is disabled or fails. A default random AI is provided.
    *   `best_snake_logic.py`: Stores the code of the current reigning champion AI. It's updated automatically when a new champion emerges. A default AI is provided.

3.  **Running Tournaments:**
    *   **Basic run (using `challenger_snake_logic.py` against current `best_snake_logic.py` or leaderboard AIs):**
        ```bash
        python main_snake_game.py
        ```
    *   **With terminal rendering (can be slow for many games):**
        ```bash
        python main_snake_game.py --render
        ```
    *   **Using LLM to generate challenger code (requires Groq API key):**
        ```bash
        python main_snake_game.py --use-llm 
        # or if API key is not an env var:
        python main_snake_game.py --use-llm --llm-api-key YOUR_GROQ_API_KEY
        ```
    *   **Adjusting games per match series in the gauntlet:**
        ```bash
        python main_snake_game.py --games_per_match 20
        ```
    *   See `python main_snake_game.py --help` for all options.

4.  **Output:**
    *   The script will print tournament progress to the console.
    *   `leaderboard.json` will be created/updated with top AIs.
    *   New champions' code will be saved with a descriptive name (e.g., `ChallengerName_GenX.py`) in the `past_champions/` directory.

## Developing Your Own Snake AI

Your AI logic is primarily implemented in a Python function with the following signature, which must be named `get_challenger_action`:

```python
# Can include standard library imports, e.g., import random, from collections import deque
# For type hinting (optional but good practice):
# from typing import List, Tuple, Optional, Deque # (Adjust Deque if needed based on actual type)
# class Snake: pass # Forward declaration for type hint
# class Food: pass  # Forward declaration for type hint

def get_challenger_action(my_snake, opponent_snake, foods, grid_width, grid_height):
    """
    Determines the next action for your snake.

    Args:
        my_snake: Your Snake object.
        opponent_snake: Opponent's Snake object. Can be None or opponent_snake.is_alive might be False.
                        Always check its status before accessing attributes.
        foods: A list of Food objects. Example: foods[0].position for the (x,y) of the first food.
               Always check if the list is empty (if foods:).
        grid_width: Integer, width of the game board.
        grid_height: Integer, height of the game board.

    Returns:
        An integer representing the chosen action:
        0: Up
        1: Right
        2: Down
        3: Left
    """
    import random # Example import

    # --- Your brilliant logic here ---

    valid_actions = my_snake.get_valid_actions()
    if not valid_actions:
        # This should ideally not happen if the snake is alive and has space.
        # Fallback to current direction if no other valid moves.
        return my_snake.direction_idx

    # Example: Simple random valid action
    chosen_action = random.choice(valid_actions)
    return chosen_action
```

**Key objects and attributes available to your AI (within `get_challenger_action`):**

*   **`my_snake` (and `opponent_snake` if not None and alive):**
    *   `positions`: `collections.deque` of `(x, y)` tuples (head is `my_snake.positions[0]`).
    *   `direction_idx`: Current direction index (0:Up, 1:Right, 2:Down, 3:Left).
    *   `length`: Integer length of the snake.
    *   `score`: Integer score (typically food eaten).
    *   `is_alive`: Boolean.
    *   `get_head_position() -> Tuple[int, int]`: Returns `(x,y)` of the snake's head.
    *   `get_valid_actions() -> List[int]`: Returns a list of valid action indices (prevents immediate 180-degree turns).
    *   `DIRECTIONS_MAP`: Class attribute `Snake.DIRECTIONS_MAP` (also accessible via `my_snake.DIRECTIONS_MAP`) = `[(0, -1), (1, 0), (0, 1), (-1, 0)]`.
    *   `ACTIONS_LIST`: Class attribute `Snake.ACTIONS_LIST` (also `my_snake.ACTIONS_LIST`) = `[0, 1, 2, 3]`.
    *   `OPPOSITE_ACTIONS_MAP`: Class attribute `Snake.OPPOSITE_ACTIONS_MAP` (also `my_snake.OPPOSITE_ACTIONS_MAP`) = `{0: 2, 1: 3, 2: 0, 3: 1}`.
    *   (Web version specifics) `grid_width`, `grid_height`: Available on the snake object itself for AIs that might need it.

*   **`Food` object (in `foods` list):**
    *   `position`: `Tuple[int, int]` representing the `(x, y)` coordinates of the food.

*   **Grid Information:**
    *   `grid_width`, `grid_height`: Passed directly as arguments.
    *   The grid is toroidal (wraps around). (0,0) is the top-left corner.

For the **local `main_snake_game.py`**, you typically place your AI code in `challenger_snake_logic.py`.
For the **web version (`index.html`)**, you create separate Python files (e.g., `my_ai.py`) inside the `past_champions/` directory and list them in `past_champions/champions_manifest.json`.

## File Structure

```
.
├── index.html                  # Web-based tournament viewer
├── main_snake_game.py          # Local Python AI competition script
├── challenger_snake_logic.py   # Your manual/experimental AI for local competition
├── best_snake_logic.py         # Current best AI (updated by main_snake_game.py)
├── leaderboard.json            # Stores top AI rankings (for local competition)
├── past_champions/             # Directory for archived champion AIs & web manifest
│   ├── champions_manifest.json # Manifest for web viewer AIs
│   ├── some_champion_ai.py     # Example AI file for web viewer / archived champion
│   └── ...
└── README.md                   # This file
```

## LLM-Powered AI Generation Notes

*   The LLM (Groq) is prompted to generate the `get_challenger_action` function.
*   It receives the game rules, snake API, game constants, and the code of the current `best_snake_logic.py` to try and improve upon it.
*   The quality of generated AIs can vary. Sometimes they are very good, other times they might have bugs or suboptimal strategies. This is part of the experiment!
*   Ensure your Groq API key is kept secret and preferably set as an environment variable.

## Future Ideas / Contributing

*   More sophisticated AI evaluation metrics.
*   Web interface for submitting AIs.
*   Support for different LLM providers.
*   Enhanced visualization and game analytics.
*   Community leaderboard online.

Contributions, bug reports, and feature requests are welcome! Please open an issue or submit a pull request.

## License

This project is currently unlicensed. Feel free to use it, but there are no explicit permissions granted for distribution or modification for other purposes.

