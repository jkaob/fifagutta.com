import os
import sys
import json
import argparse
from src.ball.ball26 import TippeData26
from src.utils import generate_files_from_tips_json


YEAR = 2026
N_MIN_HOURS = 0.25
N_MAX_DAYS = 31
VERBOSE = True

def main():
    parser = argparse.ArgumentParser(description='FifaGutta CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # csv command
    subparsers.add_parser('csv', help='Update CSV')

    # kampspill command
    kampspill_parser = subparsers.add_parser('kampspill', help='Update match schedule and player scores')
    kampspill_parser.add_argument('-n', '--n-days', type=int, default=N_MAX_DAYS,
                                  help=f'Max days to fetch (default: {N_MAX_DAYS})')

    # fetch_tips command
    subparsers.add_parser('fetch_tips', help='Fetch tips from DB and save to JSON')

    args = parser.parse_args()

    if args.command == 'csv':
        print("updating csv")
        TippeData26.action_update_csv(dir_prefix=os.getenv('GITHUB_WORKSPACE'), backup_only=False)

    elif args.command == 'kampspill':
        print("updating match schedule")
        from src.db.db_functions import add_matches_to_db, update_player_scores
        from app import app
        
        n_days = args.n_days
        print(f"Adding games for the next {n_days} days")
        
        with app.app_context():
            add_matches_to_db(n_days, N_MIN_HOURS, VERBOSE)
            print("Updating player scores")
            update_player_scores()


    elif args.command == 'fetch_tips':
        print("fetching tips from db and saving to json")
        from src.db.db_functions import get_latest_predictions_formatted
        
        with app.app_context():
            tips = get_latest_predictions_formatted()
            output_path = f"cache/tips{YEAR}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(tips, f, indent=2, ensure_ascii=False)

        print("prettyfying ...")
        generate_files_from_tips_json(YEAR)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()