import data.tips25
from tippedata import TippeData
from common import Team


class TippeData25(TippeData):
    def __init__(self, debug=False):
        year = 2025
        entries = data.tips25.ENTRIES
        teams = [
            Team('Stabæk', 'STB'),
            Team('Aalesund', 'AFK'),
            Team('Egersund', 'EGE'),
            Team('Hødd', 'HDD'),
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

        action_update_csv(backup_only=False)


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
