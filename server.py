import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from collections import defaultdict, OrderedDict
import os
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

class PitchingStats:
    def __init__(self, json_data):
        """Initialize with JSON data instead of a file."""
        self.data = json_data  # Directly store passed JSON
        self.stats = OrderedDict()  # Maintain insertion order
        self.calculate_stats()

    def calculate_stats(self):
        """Compute all pitching statistics from at-bat data."""
        at_bats = self.data.get("at_bats", {})

        total_pitches = 0
        total_strikes = 0
        total_first_pitch_strikes = 0
        total_first_pitch_fastballs = 0
        total_first_pitch_fastball_strikes = 0
        total_swings = 0
        total_swing_and_misses = 0
        total_at_bats = len(at_bats)
        total_strikeouts = 0
        total_walks = 0
        total_hbp = 0
        total_hits = 0
        total_balls_in_play = 0
        fastball_count = 0
        fastball_k_count = 0
        changeup_count = 0
        changeup_k_count = 0
        curveball_count = 0
        curveball_k_count = 0
        slider_count = 0
        slider_k_count = 0
        pitches_less_than_4 = 0
        one_one_counts = 0
        one_one_won = 0
        total_adv_count_02_12 = 0
        adv_won_out = 0
        adv_won_k = 0
        hits_on_fb = 0
        hits_on_bb = 0

        for ab_id, ab in at_bats.items():
            pitches = ab["pitch_types"]
            outcomes = ab["pitch_outcomes"]
            result = ab["at_bat_outcome"]

            total_pitches += len(pitches)

            if result == "K":
                total_strikeouts += 1
            if result == "BB":
                total_walks += 1
            if result == "HBP":
                total_hbp += 1
            if result in ("1B", "2B", "3B", "HR"):  # Hit types
                total_hits += 1
                if pitches[-1] == 1:
                    hits_on_fb += 1
                else:
                    hits_on_bb += 1
            if len(pitches) < 4:
                pitches_less_than_4 += 1

            if outcomes[0] != "B":
                total_first_pitch_strikes += 1
            if pitches[0] == 1:
                total_first_pitch_fastballs += 1
            if outcomes[0] != "B" and pitches[0] == 1:
                total_first_pitch_fastball_strikes += 1

            if result in ("1B", "2B", "3B", "HR", "GO", "FO", "LO"):
                total_balls_in_play += 1

            balls = 0
            strikes = 0
            current_adv_count = False
            for i, pitch in enumerate(pitches):
                if pitch == 1:
                    fastball_count += 1
                    if outcomes[i] != "B":
                        fastball_k_count += 1
                elif pitch == 2:
                    curveball_count += 1
                    if outcomes[i] != "B":
                        curveball_k_count += 1
                elif pitch == 3:
                    slider_count += 1
                    if outcomes[i] != "B":
                        slider_k_count += 1
                elif pitch == 4:
                    changeup_count += 1
                    if outcomes[i] != "B":
                        changeup_k_count += 1

                # Count balls and strikes
                if outcomes[i] == "B":
                    balls += 1
                else:
                    strikes += 1  # Everything else is a non-ball (strike, foul, in-play)
                    total_strikes += 1  # New: Count total strikes

                if outcomes[i] in ("S", "F", "P"):
                    total_swings += 1
                if outcomes[i] == "S":
                    total_swing_and_misses += 1

                # Track advantage counts (0-2, 1-2)
                if strikes == 2:
                    if (i == 1 and len(pitches) > 2) or (i == 2 and len(pitches) > 3):
                        total_adv_count_02_12 += 1
                        current_adv_count = True

                # Track 1-1 counts & check if the next pitch is a strike
                if balls == 1 and strikes == 1:
                    one_one_counts += 1
                    if i + 1 < len(outcomes) and outcomes[i + 1] != "B":
                        one_one_won += 1

                # Check the result of the at-bat during an advantage count
            if current_adv_count:
                if result not in ("1B", "2B", "3B", "HR", "BB", "HBP"):  # Batter got out
                    adv_won_out += 1
                if result == "K":  # Strikeout
                    adv_won_k += 1
                current_adv_count = False

        # Compute percentages
        fb_thrown = (fastball_count / total_pitches) * 100 if total_pitches > 0 else 0
        fb_for_k = (fastball_k_count / fastball_count) * 100 if fastball_count > 0 else 0
        ch_thrown = (changeup_count / total_pitches) * 100 if total_pitches > 0 else 0
        ch_for_k = (changeup_k_count / changeup_count) * 100 if changeup_count > 0 else 0
        curve_thrown = (curveball_count / total_pitches) * 100 if total_pitches > 0 else 0
        curve_for_k = (curveball_k_count / curveball_count) * 100 if curveball_count > 0 else 0
        slider_thrown = (slider_count / total_pitches) * 100 if total_pitches > 0 else 0
        slider_for_k = (slider_k_count / slider_count) * 100 if slider_count > 0 else 0
        strike_percentage = (total_strikes / total_pitches) * 100 if total_pitches > 0 else 0
        first_pitch_strike_percentage = (total_first_pitch_strikes / total_at_bats) * 100 if total_at_bats > 0 else 0
        first_pitch_fastball_percentage = (total_first_pitch_fastballs / total_at_bats) * 100 if total_at_bats > 0 else 0
        first_pitch_fastball_strike_percentage = (total_first_pitch_fastball_strikes / total_first_pitch_fastballs) * 100 if total_first_pitch_fastballs > 0 else 0
        whiff_percentage = (total_swing_and_misses / total_swings) * 100 if total_swings > 0 else 0
        batting_avg = (total_hits / (total_at_bats - total_walks - total_hbp)) if total_at_bats > 0 else 0
        babip = (total_hits / total_balls_in_play) if total_balls_in_play > 0 else 0
        on_base_percentage = ((total_hits + total_walks + total_hbp)/ total_at_bats) if total_at_bats > 0 else 0

        # Store values in ordered dictionary
        self.stats.update(OrderedDict([
            ("# Pitches Thrown", total_pitches),
            ("# Plate Appearances", total_at_bats),
            ("K", total_strikeouts),
            ("BB", total_walks),
            ("HBP", total_hbp),
            ("H", total_hits),
            ("OBP", round(on_base_percentage,3)),
            ("Batting Average", round(batting_avg,3)),
            ("BABIP", round(babip, 3)),
            ("% Strikes", round(strike_percentage, 2)),
            ("% First Pitch Strikes", round(first_pitch_strike_percentage, 2)),
            ("% First Pitch Fastballs", round(first_pitch_fastball_percentage, 2)),
            ("% First Pitch Fastball Strikes", round(first_pitch_fastball_strike_percentage, 2)),
            ("% Whiff", round(whiff_percentage, 2)),
            ("% FB Thrown", round(fb_thrown, 2)),
            ("% FB for K", round(fb_for_k, 2)),
            ("% CH Thrown", round(ch_thrown, 2)),
            ("% CH for K", round(ch_for_k, 2)),
            ("% Curveball Thrown", round(curve_thrown, 2)),
            ("% Curveball for K", round(curve_for_k, 2)),
            ("% Slider Thrown", round(slider_thrown, 2)),
            ("% Slider for K", round(slider_for_k, 2)),
            ("# 1-1 Counts", one_one_counts),
            ("1-1 Counts Won", one_one_won),
            ("ADV Counts 0-2, 1-2", total_adv_count_02_12),
            ("ADV Counts Won (Out)", adv_won_out),
            ("ADV Counts Won (K)", adv_won_k),
            ("Batters < 4 Pitches", pitches_less_than_4),
            ("Hits on FB", hits_on_fb),
            ("Hits on BB", hits_on_bb),
        ]))


def generate_game_chart(game_data, output_pdf_path):
    """Generates a game chart from JSON and saves it as a PDF."""

    # Constants for grid layout
    rows, cols = 9, 5  # 5 columns, 9 rows
    cell_width, cell_height = 180, 140  # Adjusted for better readability
    padding = 20  # Padding around the grid

    # Create a blank white image
    img_width = cols * cell_width + 2 * padding
    img_height = rows * cell_height + 2 * padding
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # Load a font for text
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font = ImageFont.load_default()

    # Function to draw at-bats
    def draw_at_bat(draw, x, y, at_bat):
        # Draw outer box
        draw.rectangle([x, y, x + cell_width, y + cell_height], outline="black", width=2)

        # Draw the mini-table for balls/strikes (10 columns x 2 rows)
        table_x, table_y = x + 10, y + 10
        box_size = 14  # Smaller boxes for 10 columns

        # Shift table to the right
        table_x = x + 30  # Moves the entire 10x2 table to the right

        # Shift "B" and "S" slightly up for better alignment
        draw.text((table_x - 20, table_y - 2), "B", fill="black", font=font)  # Balls (Top row)
        draw.text((table_x - 20, table_y + box_size - 2), "S", fill="black", font=font)  # Strikes (Bottom row)

        # Draw grid for the mini-table
        for i in range(2):  # 2 rows (balls, strikes)
            for j in range(10):  # 10 columns for pitches
                cell_x = table_x + j * box_size
                cell_y = table_y + i * box_size
                draw.rectangle([cell_x, cell_y, cell_x + box_size, cell_y + box_size], outline="black", width=1)

        # Populate pitch sequence into the mini-table (left to right)
        pitch_types = at_bat.get("pitch_types", [])
        pitch_outcomes = at_bat.get("pitch_outcomes", [])

        for idx, (pitch, outcome) in enumerate(zip(pitch_types, pitch_outcomes)):
            if idx >= 10:
                break  # Only handle up to 10 pitches

            pitch_label = str(pitch)

            # Adjust text placement to center numbers inside boxes
            box_center_offset = box_size // 2 - 6  # Center adjustment

            if outcome in ["B"]:  # Balls in **Top Row**
                text_x = table_x + idx * box_size + box_center_offset
                text_y = table_y + box_center_offset - 2
                draw.text((text_x, text_y), pitch_label, fill="black", font=font)

            elif outcome in ["S", "K", "F", "P"]:  # Strikes in **Bottom Row**
                text_x = table_x + idx * box_size + box_center_offset
                text_y = table_y + box_size + box_center_offset - 2
                # Define colors for pitch outcomes
                color_map = {
                    "S": "green",  # Swing and Miss
                    "F": "orange",  # Foul Ball
                    "P": "red",  # In Play
                }

                # Get color for this outcome (default to black if not specified)
                text_color = color_map.get(outcome, "black")

                # Draw text with the corresponding color
                draw.text((text_x, text_y), pitch_label, fill=text_color, font=font)

        # Load a larger font for the at-bat result
        try:
            result_font = ImageFont.truetype("arial.ttf", 26)  # Increased font size
        except IOError:
            result_font = ImageFont.load_default()

        # Draw the at-bat result in the center of the cell
        result = at_bat.get("at_bat_outcome", "")
        result_x = x + cell_width // 2 - 15  # Adjust for better centering
        result_y = y + cell_height // 2 - 10  # Move slightly higher
        draw.text((result_x, result_y), result, fill="black", font=result_font)

    # Place at-bats into the 5x9 grid (COLUMN-WISE FILL)
    at_bat_ids = list(game_data["at_bats"].keys())
    index = 0

    for j in range(cols):  # Move column-wise first
        for i in range(rows):  # Fill downward in each column
            if index < len(at_bat_ids):
                at_bat_id = at_bat_ids[index]
                at_bat_data = game_data["at_bats"][at_bat_id]
                draw_at_bat(draw, padding + j * cell_width, padding + i * cell_height, at_bat_data)
                index += 1

    # Add a key (legend) in the top-right corner
    key_x, key_y = img_width - 190, 30  # Position in the top-right
    key_spacing = 25  # Space between each line

    # Define the legend items (outcome → description + color)
    legend_items = [
        ("S", "Swing and Miss", "green"),
        ("F", "Foul Ball", "orange"),
        ("P", "In Play", "red"),
    ]

    # Draw a title for the key
    draw.text((key_x, key_y - 25), "Key:", fill="black", font=font)

    # Draw each legend item
    for i, (symbol, desc, color) in enumerate(legend_items):
        y_pos = key_y + i * key_spacing

        # Draw colored box
        draw.rectangle([key_x, y_pos, key_x + 15, y_pos + 15], fill=color, outline="black")

        # Draw text next to it
        draw.text((key_x + 20, y_pos), f"{symbol}: {desc}", fill="black", font=font)

    # Save as PDF
    img.convert("RGB").save(output_pdf_path)
    return output_pdf_path


@app.route("/generate-game-chart", methods=["POST"])
def generate_game_chart_route():
    """Endpoint to generate a game chart and return as a PDF."""
    try:
        game_data = request.json
        output_pdf_path = "game_chart.pdf"
        generate_game_chart(game_data, output_pdf_path)
        return send_file(output_pdf_path, mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/compute-stats', methods=['POST'])
def compute_stats():
    try:
        json_data = request.json
        stats_tracker = PitchingStats(json_data)

        # Convert OrderedDict to JSON
        response = json.dumps(stats_tracker.stats, indent=4)

        print("Returning JSON Response:")
        print(response)

        return app.response_class(response=response, mimetype="application/json")

    except Exception as e:
        print("Error processing stats:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "Flask app is running!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Get PORT from Railway
    app.run(host="0.0.0.0", port=port, debug=True)
