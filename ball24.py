import requests
from bs4 import BeautifulSoup
import shutil
import csv
import data.tips24
from common import TippeData, Scraper, Team, Contestant
from reader import CsvReader24
import os
import datetime

# get current standings every day
# check each team n matches played
# if a team has increased the number of matches played
#       check points (do we need (W/D/L) ? )
#       check goal diff
#       save data to file
# if all teams have played N matches
#       compute standings after that
#       update team position

# for each round that everyone has played
#       get position
#       compute history


class Scraper24(Scraper):
    def __init__(self) -> None:
        super().__init__('https://www.obos-ligaen.no/resultater', 'data/2024.csv')
    

    def get_standings(self):
        r = requests.get(self.url)
        soup = BeautifulSoup(r.content, 'html.parser', from_encoding='utf-8')
        league_table = soup.find('table', class_="table--persist-area table table--league-obos")
        standings = []
        for tbody in league_table.find_all("tbody"):
            # ea row has all info we need
            # iterate over each team
            for row in tbody.find_all("tr", class_="table__row"):
                team_element = row.find("span", class_="table__typo--full")
                assert team_element is not None, "Expected to find team"
                name = team_element.string # team name

                td_elements = row.find_all("td") # get number data
                n_exp = 11
                assert len(td_elements) == n_exp, f"Expected {n_exp} elements, found  {len(td_elements)}"
                pos = int(td_elements[0].get_text())
                n_played = int(td_elements[2].get_text())
                goal_diff = int(td_elements[-3].get_text())
                n_points = int(td_elements[-2].get_text())
                # Append team status to current standings
                team = [pos, name, n_played, goal_diff, n_points]
                standings.append(team)
        return standings




class TippeData24(TippeData):
    def __init__(self, debug=False):
        super().__init__(debug)
        self.teams = [
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
        self.reader = CsvReader24("data/2024.csv", self.teams, self.debug)
        self.scraper = Scraper24()

        entries = data.tips24.ENTRIES # {Name: List[team_name]}
        self.prepare_contestant_entries(entries)

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
    def update_contestants(self, input_fname=""):
        self.fetch_standings() # get latest standings online
        self.update_current_points()  # compute current points of contestants
        # Assuming CSV file has been updated
        self.compute_contestant_points_timeseries(input_fname=input_fname)
        print(f"computed contestants' points history")


def action_update_csv(dir_prefix=None, backup_only=True):
    if (dir_prefix is None):
        dir_prefix = os.getcwd()

    ball = TippeData24()

    now = datetime.datetime.now()

    backup_dir = f"{dir_prefix}/data/backup/time"  # Adjust the directory path
    os.makedirs(backup_dir, exist_ok=True)  # Ensure the backup directory exists
    backup_time = f"{backup_dir}/2024-{now.month:02d}-{now.day:02d}-{now.hour:02d}:{now.minute:02d}.csv"

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
        full_csv_path = f"{dir_prefix}/data/2024.csv"
        shutil.copy(ball.reader.csv, full_csv_path)
        print(f"\nSaved CSV file at {full_csv_path}")

    if updated_pos:
        num = ball.reader.get_n_pos_rows_written()
        backup = f"{dir_prefix}/data/backup/2024-r{num}.csv"
        shutil.copy(ball.reader.csv, backup)
        print(f"\nBackup file at {backup}")








def main():
    debug = False
    ball = TippeData24(debug)

    if debug:
        temp_fname = "data/2024-debug.csv"

        print("\n  # Fetch standings")
        ball.fetch_standings()
        ball.print_standings()

        print(f"\n  # Update {temp_fname} with latest games")
        ball.update_csv(input_fname=temp_fname, output_fname=temp_fname)
        ball.update_contestants(input_fname=temp_fname)

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

    #print("\n  # Update points of contestants")
    #ball.update_current_points()
    #ball.print_contestants()


    
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
