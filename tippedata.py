import csv
import shutil
import os
import datetime


from common import Scraper, Contestant, Team
from reader import CsvReader


#  can we combine this with derived class  ?
class TippeDataBase:

    def __init__(self, debug=False):
        self.debug = debug
        self.scraper = None #Scraper()  # to get table
        self.reader = None
        # Initialize dict with points computation

        # list of Contestant objects, each with their betting data
        self.contestants = []

        # Initialize teams list with url to match history
        #self.data_dict = {} # key: name. value: contestants.data
        self.teams = []
        self.min_played = 0
        self.standings = []  # [ [pos, name, n_played, goal_diff, n_points] ]
        self.standings_simple = []

    def set_contestant(self, contestant):
        for c in self.contestants:
            if c.name == contestant.name:
                print(f"contestant {c.name} already added")
                return
        self.contestants.append(contestant)

    def get_contestant(self, name):
        for c in self.contestants:
            if c.name == name:
                return c

    def get_team(self, team_name):
        for team in self.teams:
            if team.name == team_name \
                or team.name.split(' ')[0] == team_name.split(' ')[0] \
                or team.name.split(' ')[0] == team_name:
                    return team
        print(f"could not find team {team_name}!")
        return None

    def get_team_short(self, team_name):
        team = self.get_team(team_name)
        if team is None or not team.short:
            print(f"could not find team {team_name} short")
            return None
        return team.short


    def fetch_standings(self):
        self.standings = self.scraper.get_standings()
        return self.standings

    def get_latest_standings_from_csv(self):
        self.standings_simple = self.reader.get_simple_standings_at_round_number(
            self.reader.get_n_pos_rows_written())
        print("STANDINGS:", self.standings_simple)


    def compute_points(self, name):
        contestant = self.get_contestant(name)
        prediction = contestant.data['prediction']
        total_points = 0
        # Select the appropriate standings and define a row extractor
        if self.standings:
            s = self.standings
            extract = lambda row: (row[1].split(" ")[0], row[0])
        elif self.standings_simple:
            s = self.standings_simple
            extract = lambda row: (row[0], row[1])
        else:
            print("no data")

        for row in s:
            team_name, team_pos = extract(row)
            team_ind = next((index for index, obj in enumerate(prediction)
                             if obj.name == team_name), None)
            if team_ind is None:
                continue  # or handle the error if the team isn't found
            prediction_pos = team_ind + 1  # Convert index to table placement
            points = abs(prediction_pos - team_pos)
            contestant.data['delta'][team_ind] = points  # store points
            contestant.data['corrects'][team_ind] = (points == 0)
            total_points += points
        contestant.data['points'] = total_points # store total points
        return total_points


    def update_current_points(self):
        for contestant in self.contestants:
            self.compute_points(contestant.name)
        # Add normalized points for visualization
        max_points = max(contestant.data['points'] for contestant in self.contestants)
        for contestant in self.contestants:
            contestant.data['normalized'] = 0.0 if max_points==0.0 else contestant.data['points'] / max_points


    def get_sorted_contestants(self):
        sorted_contestants = sorted(self.contestants, key=lambda contestant: contestant.data['points'])
        return sorted_contestants

    def get_sorted_names(self):
        # Sort the contestants based on 'points' and return their names
        return [contestant.name for contestant in self.get_sorted_contestants()]




    def print_standings(self):
        header = "{:<4} {:<15} {:<7} {:<4} {:<6}".format("POS", "TEAM", "PLAYED", "GD", "POINTS")
        print(header)
        for r in self.standings:
            line = "{:<4} {:<15} {:<7} {:<4} {:<6}".format(*r)
            print(line)
        print("-" * len(header))

    def print_contestants(self):
        print("---Current leaderboard---")
        for c in self.get_sorted_contestants():
            print(f"{c.name}: {c.data['points']} points")
        print("-------------------------")






class TippeData(TippeDataBase):
    def __init__(self, year, entries_dict, teams_list, debug=False):
        super().__init__(debug)
        self.teams = teams_list
        self.year = year
        self.reader = CsvReader(f"data/{self.year}.csv", self.teams, self.debug)
        self.scraper = Scraper(year)

        entries = entries_dict #data.tips24.ENTRIES # importing from data/  # {Name: List[team_name]}
        self.prepare_contestant_entries(entries)
        self.set_contestant(self.create_average_contestant())

    def create_average_contestant(self):
        for team in self.teams:
            team.avg_placement = 0
        for contestant in self.contestants:
            for index, team in enumerate(contestant.data['prediction']):
                self.teams[self.teams.index(team)].avg_placement += (index + 1)
        for team in self.teams:
            team.avg_placement = team.avg_placement / (float)(len(self.teams))

        # sort teams based on their avg_placement in rising order
        sorted_teams = sorted(self.teams, key=lambda x: x.avg_placement)
        avg_contestant = Contestant("fifagutta", "AVG")
        avg_contestant.set_prediction(sorted_teams)

        # Optionally, print each team's average placement for verification
        if self.debug:
            for team in sorted_teams:
                print("team", team.name, "avg:", team.avg_placement)
        # Return or store the average contestant
        return avg_contestant


    def prepare_contestant_entries(self, entries):
        if not self.teams:
            print(f"teams not set! cant set data dict")
            return
        # entries: {Name: { prediction: [], short: "", avatar : ""} }
        for name, data in entries.items():
            contestant = Contestant(name, data['short'])
            contestant.set_avatar(data['avatar'])
            prediction = []
            for team_name in data['prediction']: # add each team in order
                team = self.get_team(team_name)
                if not team:
                    print(f"did not find team {team_name}")
                    return
                prediction.append(team)
            contestant.set_prediction(prediction)
            # add contestant to list of contestants
            self.set_contestant(contestant)

    # update CSV file from current standings for each team not already updated
    def update_team_csv(self, output_fname="", input_fname=""):
        updated_something = False

        # use a temp file to write/read so that we dont refresh
        temp_path = None
        if output_fname != input_fname:
            temp_path = "data/temp.csv"
            if not input_fname:
                input_fname = self.reader.csv
            # copy file at path input_fname to path temp_path
            shutil.copyfile(input_fname, temp_path)

        for team in self.teams:
            # find the row in standings for this teame
            team_standing = None
            for standing in self.standings:
                if team.name == standing[1] or team.name == standing[1].split(" ")[0]:  # team name is at index 1
                    team_standing = standing
                    break  # Exit loop once the matching team is found
            if team_standing is None:
                raise ValueError(f"ERROR did not find team {team.name} in standings")

            team.n_played = int(team_standing[2])
            csv_n_played = self.reader.get_n_matches_played(team.name, input_fname)
            if (team.n_played == csv_n_played):
                if self.debug:
                    print(f"already saved round {team.n_played} for {team.name}\n")
                continue # already saved last match played - continue

            f_in = temp_path if temp_path is not None else input_fname
            f_out = temp_path if temp_path is not None else output_fname

            self.reader.write_team_entry(
                team.name, team.n_played, team_standing[4], team_standing[3],
                output_fname=f_out, input_fname=f_in)
            updated_something = True

        if temp_path is not None:
            shutil.copyfile(temp_path, output_fname)
            print(f"->copied {temp_path} to {output_fname}")
        return updated_something

    def compute_standings_after_full_round(self, round_number, input_fname=""):
        # read historic data
        for team in self.teams:
            csv_entry = self.reader.get_team_entry(team.name, round_number, input_fname=input_fname)
            if csv_entry is None:
                print("ERROR: Returning")
                return
            match_data = {
                'points': int(csv_entry[2]),
                'gd': int(csv_entry[3]),
                'pos': None # update later
            }
            team.match_history[round_number] = match_data
        # compute positions based on round data
        round_standings = []  # name, points, gd
        for team in self.teams:
            round_standings.append([team.name,
                                    team.match_history[round_number]['points'],
                                    team.match_history[round_number]['gd']])
        # sort on points first and gd second
        round_standings.sort(key=lambda x: (x[1], x[2]), reverse=True)
        if self.debug:
            print(f"Game #{round_number}:\n# |  Team  | Points | GD")
        # save team positions for this round
        for i in range(len(round_standings)):
            team = self.get_team(round_standings[i][0])
            team.match_history[round_number]['pos'] = i+1
            if self.debug:
                print(f"{i+1}| {round_standings[i]}")


    # check CSV file, find min_played for all teams; check if min_played has "pos" for each team
    # if not, need to add "pos" for the teams
    # return if something was updated
    def update_csv_positions(self, output_fname="", input_fname=""):

        n_registered_matches = self.reader.get_min_matches_played(input_fname=input_fname)
        n_registered_positions = self.reader.get_n_pos_rows_written(input_fname=input_fname)
        if self.debug:
            print(f"already registered {n_registered_matches} matches")
        if n_registered_matches == n_registered_positions:
            print(f"->latest position already updated")
            return False


        if abs(n_registered_positions-n_registered_matches) > 1:
            print(f"WARN: registered matches is {n_registered_matches} but registered positions is only {n_registered_positions} ")

        # Compute positions for all rounds that havent gotten this
        for round_number in range(n_registered_positions+1, n_registered_matches+1):
            self.compute_standings_after_full_round(round_number, input_fname)

        # use a temp file to write/read so that we dont refresh
        temp_path = None
        if output_fname != input_fname:
            temp_path = "data/temp.csv"
            if not input_fname:
                input_fname = self.reader.csv
            # copy file at path input_fname to path temp_path
            shutil.copyfile(input_fname, temp_path)

        f_in = temp_path if temp_path is not None else input_fname
        f_out = temp_path if temp_path is not None else output_fname

        # Update "pos" column for each team
        for team in self.teams:
            self.reader.write_team_pos(team.name, round_number,
                                       team.match_history[round_number]['pos'],
                                       output_fname=f_out, input_fname=f_in)

        if temp_path is not None:
            shutil.copyfile(temp_path, output_fname)
            print(f"->copied {temp_path} to {output_fname}")

        if self.debug:
            print(f"->added 'pos' for each team round {n_registered_matches}")
        return True


    # compute the points_history for each contestant, using csv positions
    def compute_contestant_points_timeseries(self, input_fname=""):
        # read csv file "POS" for i in range(n_min_played)
        n_pos_written = self.reader.get_n_pos_rows_written(input_fname=input_fname)

        for contestant in self.contestants:
            contestant.data['points_history'] = [] # empty previous stuff

        for round_number in range(1, n_pos_written+1):
            round_standings = self.reader.get_simple_standings_at_round_number(round_number, input_fname=input_fname)

            if self.debug:
                print("Round", round_number, "standings:", round_standings)

            #compute points for each contestants using those standings
            for contestant in self.contestants:
                prediction = contestant.data['prediction']
                round_points = 0
                for row in round_standings:
                    team_name = row[0]
                    team_ind = next((index for index, obj in enumerate(prediction) \
                                    if obj.name == team_name), None)
                    prediction_pos = team_ind + 1
                    team_pos = int(row[1])
                    team_points = abs(prediction_pos - team_pos)
                    round_points += team_points
                # append round points to history
                contestant.data['points_history'].append(round_points)



    # TO BE RUN BY WORKFLOW
    def update_csv(self, output_fname="", input_fname=""):
        self.fetch_standings()

        if (output_fname=="" and input_fname==""):
            output_fname = self.reader.csv
            input_fname = self.reader.csv

        updated_matches = self.update_team_csv(
            output_fname=output_fname, input_fname=input_fname)

        updated_pos =  self.update_csv_positions(
            output_fname=output_fname, input_fname=output_fname)

        if updated_matches:
            print(f"updated matches of file  {output_fname or self.reader.csv}")
        if updated_pos:
            print(f"updated positions of file  {output_fname or self.reader.csv}")
        return updated_pos, updated_matches

    # MAIN FCN - RUN AT REFRESH
    def update_contestants(self, fetch=True, input_fname=""):
        if (fetch):
            self.fetch_standings() # get latest standings online
        else:
            self.get_latest_standings_from_csv()

        self.update_current_points()  # compute current points of contestants
        # Assuming CSV file has been updated
        self.compute_contestant_points_timeseries(input_fname=input_fname)
        print(f"computed contestants' points history")




    @staticmethod
    def action_update_csv(year, dir_prefix=None, backup_only=True):
        if (dir_prefix is None):
            dir_prefix = os.getcwd()

        ball = TippeData(year)

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
