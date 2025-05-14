import data.tips24
from .tippedata import TippeData
from .common import Team


class TippeData24(TippeData):
    def __init__(self, debug=False):
        year = 2024
        entries = data.tips24.ENTRIES
        teams = [
            Team('Stabæk', 'STB'),
            Team('Aalesund', 'AFK'),
            Team('Bryne', 'BRY'),
            Team('Egersund', 'EGE'),
            Team('Kongsvinger', 'KIL'),
            Team('Levanger', 'LEV'),
            Team('Lyn', 'LYN'),
            Team('Mjøndalen', 'MIF'),
            Team('Moss', 'MOS'),
            Team('Ranheim TF', 'RAN'),
            Team('Raufoss', 'RAU'),
            Team('Sandnes Ulf', 'ULF'),
            Team('Sogndal', 'SGN'),
            Team('Start', 'STA'),
            Team('Vålerenga', 'VIF'),
            Team('Åsane', 'ÅSA'),
        ]
        super().__init__(year, entries, teams, debug)




def main():
    debug = True
    ball = TippeData24(debug)

    if debug:
        temp_fname = "data/2024-debug.csv"

        print("\n  # Fetch standings")
        ball.fetch_standings()
        ball.print_standings()

        print(f"\n  # Update {temp_fname} with latest games")
        # ball.update_csv(input_fname=temp_fname, output_fname=temp_fname)
        #ball.update_contestants(input_fname=temp_fname)

    else:
        print("\nFETCHING STANDINGS AND UPDATING CSV\n")

        action_update_csv(backup_only=False)

        # update MAIN csv
        # updated_pos, updated_mathces = ball.update_csv()

        # if updated_matches or updated_pos:
        #     backup = f"data/backup/2024-{MONTH}-{DAY}-{HOUR}:{MINUTE}"
        #     shutil.copy(ball.reader.csv, backup)
        #     print(f"\nBackup file at {backup}")

        # if updated_pos:
        #     num = ball.reader.get_n_pos_rows_written()
        #     backup = f"data/backup/2024-r{num}"
        #     shutil.copy(ball.reader.csv, backup)
        #     print(f"\nBackup file at {backup}")

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
