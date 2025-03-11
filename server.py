import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import defaultdict, OrderedDict

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

        # Store values in ordered dictionary
        self.stats.update(OrderedDict([
            ("# Pitches Thrown", total_pitches),
            ("# ABs", total_at_bats),
            ("K", total_strikeouts),
            ("BB", total_walks),
            ("HBP", total_hbp),
            ("H", total_hits),
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


if __name__ == '__main__':
    app.run(debug=True)
