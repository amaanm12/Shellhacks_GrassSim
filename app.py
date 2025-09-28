import copy
import random
from flask import Flask, jsonify, render_template, request

# --- App Setup ---
app = Flask(__name__)

# --- Game Configuration ---
GRID_SIZE = 5  # Changed from 10 to 5
WATER_COST = 10
WATER_REPLENISH = 30

# Define a function to create the initial state, so resetting is easy
def create_initial_state():
    return {
        "day": 1,
        "aquifer_level": 100,
        "weather": "Sunny",
        "lawn_grid": [
            {"type": "grass", "moisture": 100, "is_mowed": False} for _ in range(GRID_SIZE * GRID_SIZE)
        ],
        "player_pos": {"x": GRID_SIZE // 2, "y": GRID_SIZE // 2},
        "game_over": False,
        "message": "Use WASD to move, Space to mow, and Enter for the next day.",
    }

# Use a deep copy to avoid modifying the original constant
game_state = create_initial_state()

# --- Backend Logic ---
def check_game_over():
    """Checks for game over conditions and updates the state."""
    global game_state
    if game_state["game_over"]:
        return

    # Condition 1: Aquifer is empty
    if game_state["aquifer_level"] <= 0:
        game_state["game_over"] = True
        game_state["aquifer_level"] = 0
        game_state["message"] = f"Game Over: The aquifer ran dry! You survived {game_state['day']} days."
        return

    # Condition 2: All grass tiles have 0 moisture (are dead)
    is_all_dead = all(tile.get("moisture", 0) == 0 for tile in game_state["lawn_grid"] if tile["type"] == "grass")
    if is_all_dead:
        game_state["game_over"] = True
        game_state["message"] = f"Game Over: Your lawn died! You survived {game_state['day']} days."


# --- API Routes ---
@app.route('/')
def index():
    """Serves the main game page."""
    return render_template('index.html')

@app.route('/gamestate')
def get_gamestate():
    """Returns the current state of the game."""
    return jsonify(game_state)

@app.route('/reset', methods=['POST'])
def reset_game():
    """Resets the game to its initial state."""
    global game_state
    game_state = create_initial_state()
    return jsonify(game_state)

@app.route('/water', methods=['POST'])
def water_lawn():
    """Waters the entire lawn, consuming aquifer water."""
    global game_state
    if not game_state["game_over"]:
        if game_state["aquifer_level"] >= WATER_COST:
            game_state["aquifer_level"] -= WATER_COST
            for tile in game_state["lawn_grid"]:
                if tile["type"] == "grass":
                    tile["moisture"] = min(100, tile["moisture"] + WATER_REPLENISH)
            game_state["message"] = f"You watered the lawn for {WATER_COST} aquifer points."
        else:
            game_state["message"] = "Not enough water in the aquifer!"
        check_game_over()
    return jsonify(game_state)


@app.route('/move', methods=['POST'])
def move_player():
    """Moves the player based on WASD input."""
    global game_state
    if not game_state["game_over"]:
        direction = request.json.get("direction")
        pos = game_state["player_pos"]
        
        if direction == 'w':
            pos['y'] = max(0, pos['y'] - 1)
        elif direction == 's':
            pos['y'] = min(GRID_SIZE - 1, pos['y'] + 1)
        elif direction == 'a':
            pos['x'] = max(0, pos['x'] - 1)
        elif direction == 'd':
            pos['x'] = min(GRID_SIZE - 1, pos['x'] + 1)
            
    return jsonify(game_state)

@app.route('/mow', methods=['POST'])
def mow_tile():
    """Toggles the 'mowed' status of the tile the player is on."""
    global game_state
    if not game_state["game_over"]:
        pos = game_state["player_pos"]
        index = pos['y'] * GRID_SIZE + pos['x']
        
        tile = game_state["lawn_grid"][index]
        if tile["type"] == "grass":
            tile["is_mowed"] = True
            game_state["message"] = "You mowed a patch of grass."
            
    return jsonify(game_state)


@app.route('/nextday', methods=['POST'])
def next_day():
    """Advances the game by one day, simulating evaporation and weather."""
    global game_state
    if not game_state["game_over"]:
        game_state["day"] += 1
        
        # Determine weather for the new day
        weather_roll = random.random()
        if weather_roll < 0.15:
            game_state["weather"] = "Rainy"
            dryness_multiplier = 0
        elif weather_roll < 0.35:
            game_state["weather"] = "Extremely Sunny"
            dryness_multiplier = 2
        else:
            game_state["weather"] = "Sunny"
            dryness_multiplier = 1

        # Update moisture based on weather and mowed status
        base_dryness = 10
        for tile in game_state["lawn_grid"]:
            if tile["type"] == "grass":
                # Mowed grass dries faster
                mow_multiplier = 2 if tile["is_mowed"] else 1
                
                total_dryness = base_dryness * dryness_multiplier * mow_multiplier
                tile["moisture"] = max(0, tile["moisture"] - total_dryness)

        game_state["message"] = f"A new day! It is day {game_state['day']}. The weather is {game_state['weather']}."
        check_game_over()
        
    return jsonify(game_state)

@app.route("/")
def home():
    # Choose a random weather condition
    weather = random.choice(["sunny", "dry", "cloudy", "rainy"])

    # Determine the lawn color change level based on weather
    if weather == "sunny":
        style = 1  # change 1 level darker
    elif weather == "dry":
        style = 2  # change 2 levels darker
    elif weather == "cloudy":
        style = 0  # no change
    elif weather == "rainy":
        style = -1  # one level lighter

    # Pass weather info to the template title and style for the lawn appearance.
    return render_template("index.html", title=f"Weather: {weather}", style=style)

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)
