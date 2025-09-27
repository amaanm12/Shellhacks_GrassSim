import copy
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

PLANT_TYPES = {
    "Dirt": {"name": "Dirt", "water_need": 0, "color": "#a1887f"},
    "St. Augustine": {"name": "St. Augustine", "water_need": 15, "color": "#4caf50"},
    "Wildflowers": {"name": "Wildflowers", "water_need": 5, "color": "#ffeb3b"},
    "Zoysia": {"name": "Zoysia", "water_need": 10, "color": "#8bc34a"},
    "Dead": {"name": "Dead", "water_need": 0, "color": "#5d4037"},
}

INITIAL_GAME_STATE = {
    "day": 1,
    "aquifer_level": 100,
    "lawn_grid": [
        {"plant_type": "St. Augustine", "moisture": 50} for _ in range(9)
    ],
    "game_over": False,
    "message": "Welcome to RootDown! Keep your lawn alive without draining the aquifer.",
}

# deep copy to avoid modifying the original constant
game_state = copy.deepcopy(INITIAL_GAME_STATE)

# --- Backend Logic ---
def check_game_over():
    """Checks for game over conditions and updates the state."""
    global game_state
    if game_state["game_over"]:
        return

    # Condition 1: Aquifer is empty
    if game_state["aquifer_level"] <= 0:
        game_state["game_over"] = True
        game_state["message"] = "Game Over: The aquifer has run dry! Your score is {} days.".format(game_state["day"])
        return

    # Condition 2: All plants are dead
    if all(tile["plant_type"] == "Dead" for tile in game_state["lawn_grid"]):
        game_state["game_over"] = True
        game_state["message"] = "Game Over: All your plants have died! Your score is {} days.".format(game_state["day"])

#api destin
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
    game_state = copy.deepcopy(INITIAL_GAME_STATE)
    return jsonify(game_state)

@app.route('/water', methods=['POST'])
def water_lawn():
    """Waters the lawn, consuming aquifer water."""
    global game_state
    if not game_state["game_over"]:
        water_amount = 10
        if game_state["aquifer_level"] >= water_amount:
            game_state["aquifer_level"] -= water_amount
            for tile in game_state["lawn_grid"]:
                if tile["plant_type"] != "Dead" and tile["plant_type"] != "Dirt":
                    tile["moisture"] = min(100, tile["moisture"] + 30)
            game_state["message"] = "You watered the lawn."
        else:
            game_state["message"] = "Not enough water in the aquifer!"
        check_game_over()
    return jsonify(game_state)

@app.route('/plant', methods=['POST'])
def plant():
    """Changes a plant on a specific tile."""
    global game_state
    if not game_state["game_over"]:
        data = request.json
        tile_index = data.get("tile_index")
        plant_name = data.get("plant_name")
        if 0 <= tile_index < len(game_state["lawn_grid"]) and plant_name in PLANT_TYPES:
            game_state["lawn_grid"][tile_index] = {"plant_type": plant_name, "moisture": 50}
            game_state["message"] = f"You planted {plant_name}."
    return jsonify(game_state)

@app.route('/nextday', methods=['POST'])
def next_day():
    """Advances the game by one day, simulating evaporation."""
    global game_state
    if not game_state["game_over"]:
        game_state["day"] += 1
        game_state["message"] = f"A new day has dawned. It is day {game_state['day']}."
        for tile in game_state["lawn_grid"]:
            plant_info = PLANT_TYPES.get(tile["plant_type"])
            if plant_info:
                tile["moisture"] = max(0, tile["moisture"] - plant_info["water_need"])
                if tile["moisture"] == 0 and tile["plant_type"] not in ["Dirt", "Dead"]:
                    tile["plant_type"] = "Dead"
        check_game_over()
    return jsonify(game_state)

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)