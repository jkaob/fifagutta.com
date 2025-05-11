from  src.ball25 import TippeData25
import os
import sys

YEAR=2025


if __name__ == "__main__":

    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "csv":
        print("updating csv")
        TippeData25.action_update_csv(dir_prefix=os.getenv('GITHUB_WORKSPACE'), backup_only=False)

    else: 
        print("updating match schedule")
        # other stuff
