import os
import sys
from src.ball.ball26 import TippeData26
from src.db.db import add_matches_to_db
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

    else: 
        print("updating match schedule")
        with app.app_context():
            add_matches_to_db(N_MAX_DAYS, N_MIN_HOURS, VERBOSE)
        