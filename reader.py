import csv
from common import Scraper, Team, Contestant
import os

class CsvReader():
    def __init__(self, filename: str, teams, debug=False):
        self.debug = debug
        self.csv = filename
        self.team_names = [t.name for t in teams]
        self.n_teams = len(self.team_names)

        if not os.path.exists(filename):
            raise FileNotFoundError(f"The file {filename} does not exist.")

    def get_team_entry(self, team_name, round_number, input_fname=""):
        if input_fname == "":
            input_fname = self.csv
        with open(input_fname, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                if row[0] == team_name and int(row[1]) == round_number:
                    if row[2] == "-":
                        print(f"WARN: entry for {team_name} round {round_number} is empty")
                    return row
        print(f"could not get entry for {team_name} round {round_number}")
        return None


    # n_matches for a specific team
    def get_n_matches_played(self, team_name, input_fname=""):
        n_matches_played = 0
        if input_fname == "":
            input_fname = self.csv
        with open(input_fname, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                if row[0] == team_name and row[2] != '-':
                    n_matches_played += 1
        if self.debug:
            print(f"{team_name} has {n_matches_played} matches saved")
        return n_matches_played

    def get_min_matches_played(self, input_fname=""):
        print("checking number of rounds played...")
        n_min = 2*(self.n_teams-1)
        for name in self.team_names:
            n_played = self.get_n_matches_played(name, input_fname)
            n_min = min(n_min, n_played)
        print(f"->all teams have played at least {n_min} rounds")
        return n_min

    # checks file, and sees how many "pos" rows have been written via fcn write_team_pos()
    # i.e. how many standings
    def get_n_pos_rows_written(self, input_fname=""):
        n_rows = None
        if input_fname == "":
            input_fname = self.csv
        with open(input_fname, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)

            current_team = None
            current_n_rows = 0
            for row in reader:
                team = row[0]
                pos = row[4]
                # every time we reach a new team
                if team != current_team:
                    # for all teams except first
                    if current_team is not None:
                        #if self.debug:
                            #print(f"{current_team} has {current_n_rows} 'pos' rows saved")
                        if n_rows is None:
                            n_rows = current_n_rows
                        elif n_rows != current_n_rows:
                            print(f"ERROR! {current_team} has {current_n_rows} but previous team had {n_rows}!")

                        current_n_rows = 0
                    current_team = team

                # check if pos has been updated
                if pos.isdigit():
                    current_n_rows += 1
            # Check the last team's 'pos' count
            if current_n_rows != n_rows and n_rows is not None:
                print(f"ERROR! {current_team} has {current_n_rows} 'pos' rows, but expected {n_rows}!")

        if self.debug and n_rows is not None:
            print(f"->{n_rows} 'pos' rows already written for each team")
        return n_rows if n_rows is not None else 0


    # get sorted list of standings at round number
    def get_simple_standings_at_round_number(self, round_number, input_fname=""):
        round_standings = []
        if input_fname == "":
            input_fname = self.csv
        with open(input_fname, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # skip header
            for row in reader:
                if int(row[1]) == round_number:
                    if row[4].isdigit():
                        round_standings.append([row[0], int(row[4])])
                    else:
                        raise ValueError(f"ERROR: round {round_number} not found for team {row[0]}")

        # sort and return
        round_standings.sort(key=lambda x: (x[1]))
        return round_standings


    def write_team_entry(self, team_name, round_number, new_points, new_gd,
                         output_fname="", input_fname=""):
        updated_rows = []
        new_row = None
        if input_fname == "":
            input_fname = self.csv
        with open(input_fname, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0] == team_name and int(row[1]) == round_number:
                    row[2] = str(new_points)  # Update points
                    row[3] = str(new_gd)  # Update goal difference
                    new_row = row
                updated_rows.append(row)
            if new_row is None:
                raise ValueError(f"ERROR: did not find row {round_number} for {team_name}!")

        # write
        if output_fname == "":
            output_fname = self.csv
        with open(output_fname, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(updated_rows)
        print(f"->wrote round {round_number} for {team_name}: {new_row}\n")


    # updates the "pos" column of a team
    def write_team_pos(self, team_name, round_number, new_position, output_fname="", input_fname=""):
        updated_rows = []
        if input_fname == "":
            input_fname = self.csv
        with open(input_fname, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0] == team_name and int(row[1]) == round_number:
                    if row[4] != "-":
                        raise ValueError(f"ERROR: {team_name} pos already set")
                    row[4] = new_position
                updated_rows.append(row)
        # write
        if output_fname == "":
            output_fname = self.csv
        with open(output_fname, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(updated_rows)
        print(f"->wrote pos at round {round_number} for {team_name}\n")
        return True
