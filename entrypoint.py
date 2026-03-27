import os
import sys
import json     
from src.ball.ball26 import TippeData26
from app import app


YEAR=2026
N_MIN_HOURS=0.25
N_MAX_DAYS=31
VERBOSE=False

if __name__ == "__main__":

    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "csv":
        print("updating csv")
        TippeData26.action_update_csv(dir_prefix=os.getenv('GITHUB_WORKSPACE'), backup_only=False)

    if arg == "kampspill":
        print("updating match schedule")
        from src.db.functions import add_matches_to_db, update_player_scores
        
        with app.app_context():
            add_matches_to_db(N_MAX_DAYS, N_MIN_HOURS, VERBOSE)
            update_player_scores()


    if arg == "fetch_tips":
        print("fetching tips from db and saving to json")
        from src.db.functions import get_latest_predictions_formatted
        with app.app_context():
            tips = get_latest_predictions_formatted()
            output_path = f"cache/tips{YEAR}.json"
            with open(output_path, "w") as f:
                json.dump(tips, f)