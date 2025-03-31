import data.tips25
from tippedata import TippeData
from common import Team
import os
import csv
import datetime
import shutil

class TippeData25(TippeData):
    def __init__(self, debug=False):
        year = 2025
        entries = data.tips25.ENTRIES
        teams = [
            Team('Stabæk', 'STB'),
            Team('Aalesund', 'AFK'),
            Team('Egersund', 'EGE'),
            Team('Hødd', 'HØD'),
            Team('Kongsvinger', 'KIL'),
            Team('Lillestrøm', 'LSK'),
            Team('Lyn', 'LYN'),
            Team('Mjøndalen', 'MIF'),
            Team('Moss', 'MOS'),
            Team('Odd', 'ODD'),
            Team('Ranheim TF', 'RAN'),
            Team('Raufoss', 'RAU'),
            Team('Skeid', 'SKE'),
            Team('Sogndal', 'SGN'),
            Team('Start', 'STA'),
            Team('Åsane', 'ÅSA'),
        ]
        super().__init__(year, entries, teams, debug)

    @staticmethod
    def action_update_csv(year, dir_prefix=None, backup_only=True):
        if (dir_prefix is None):
            dir_prefix = os.getcwd()

        ball = TippeData25(year)

        now = datetime.datetime.now()

        backup_dir = f"{dir_prefix}/data/backup/time"  # Adjust the directory path
        os.makedirs(backup_dir, exist_ok=True)  # Ensure the backup directory exists
        backup_time = f"{backup_dir}/{year}-{now.month:02d}-{now.day:02d}-{now.hour:02d}.{now.minute:02d}.csv"

        if backup_only:
            ball.update_csv(output_fname=backup_time)
            return

        # update main CSV file here
        updated_pos, updated_matches = ball.update_csv()

        if updated_matches or updated_pos:
            # make backup whenever something has changed
            shutil.copy(ball.reader.csv, backup_time)
            print(f"\nBackup file at {backup_time}")

            # Hotfix - use full path to ensure stuff is saved
            full_csv_path = f"{dir_prefix}/data/{year}.csv"
            try:
                shutil.copy(ball.reader.csv, full_csv_path)
                print(f"\nSaved CSV file at {full_csv_path}")
            except:
                print(f"\nFile should be found at {full_csv_path}")
                pass

        if updated_pos:
            num = ball.reader.get_n_pos_rows_written()
            backup = f"{dir_prefix}/data/backup/{year}-r{num}.csv"
            shutil.copy(ball.reader.csv, backup)
            print(f"\nBackup file at {backup}")




def main():
    debug = True
    ball = TippeData25(debug)

    if debug:
        temp_fname = "data/2025-debug.csv"

        print("\n  # Fetch standings")
        ball.fetch_standings()
        ball.print_standings()

        print(f"\n  # Update {temp_fname} with latest games")

    else:
        print("\nFETCHING STANDINGS AND UPDATING CSV\n")

        ball.action_update_csv(backup_only=False)


    print("\n  # Update points of contestants")
    ball.update_current_points()
    ball.print_contestants()



    # print("\n  # Get number of Pos Rows Written")
    # ball.reader.get_n_pos_rows_written()

    # print("\n  # Compute Standings After Full Round")
    # ball.compute_standings_after_full_round(round_number=1)

    # print("\n  # Update CSV positions")
    # ball.update_csv_positions()

    # print("\n  # Compute Contestant Timeseries")
    # ball.compute_contestant_points_timeseries()



if __name__ == "__main__":
    main()
