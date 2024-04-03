import requests
from bs4 import BeautifulSoup
import csv
import data.tips24
from common import TippeData, Scraper, Team, Contestant

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


class CsvReader24():
    def __init__(self, filename: str, teams, debug=False):
        self.debug = debug
        self.csv = filename
        self.team_names = [t.name for t in teams]
        self.n_teams = len(self.team_names)

    def get_team_entry(self, team_name, round_number):
        with open(self.csv, 'r', encoding='utf-8') as f:
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
    def get_n_matches_played(self, team_name):
        n_matches_played = 0
        with open(self.csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                if row[0] == team_name and row[2] != '-':
                    n_matches_played += 1
        if self.debug:
            print(f"{team_name} has played {n_matches_played} matches")
        return n_matches_played
    
    def get_min_matches_played(self):
        print("checking number of rounds played...")
        n_min = 2*(self.n_teams-1)
        for name in self.team_names:
            n_played = self.get_n_matches_played(name)
            n_min = min(n_min, n_played)
        print(f"->all teams have played at least {n_min} rounds")
        return n_min
    
    # checks file, and sees how many "pos" rows have been written via fcn write_team_pos()
    # i.e. how many standings
    def get_n_pos_rows_written(self):
        n_rows = None
        with open(self.csv, 'r', newline='', encoding='utf-8') as f:
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
            print(f"{n_rows} 'pos' rows have been written for each team")
        return n_rows if n_rows is not None else 0
    
    
    # get sorted list of standings at round number
    def get_simple_standings_at_round_number(self, round_number):
        round_standings = []
        with open(self.csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # skip header
            for row in reader:
                if int(row[1]) == round_number:
                    if row[4].isdigit():
                        round_standings.append([row[0], int(row[4])])
                    else:
                        print(f"ERROR: round {round_number} not found for team {row[0]}")
        # sort and return
        round_standings.sort(key=lambda x: (x[1]))
        return round_standings
    

    def write_team_entry(self, team_name, round_number, new_points, new_gd):
        updated_rows = []
        with open(self.csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0] == team_name and int(row[1]) == round_number:
                    row[2] = new_points  # Update points
                    row[3] = new_gd  # Update goal difference
                updated_rows.append(row)
        with open(self.csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(updated_rows)
        print(f"->added round {round_number} for {team_name}\n")


    # updates the "pos" column of a team
    def write_team_pos(self, team_name, round_number, new_position):
        updated_rows = []
        with open(self.csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0] == team_name and int(row[1]) == round_number:
                    if row[4] != "-":
                        print(f"{team_name} pos already set")
                        return False
                    row[4] = new_position  
                updated_rows.append(row)
        with open(self.csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(updated_rows)
        print(f"->updated position at round {round_number} for {team_name}\n")
        return True




class TippeData24(TippeData):
    def __init__(self, debug=False):
        super().__init__(debug)
        self.teams = [
            Team('Aalesund', 'AAFK'),
            Team('Bryne', 'BRY'),
            Team('Egersund', 'EGER'),
            Team('Kongsvinger', 'KIL'),
            Team('Levanger', 'LEV'),
            Team('Lyn', 'LYN'),
            Team('Mjøndalen', 'MIF'),
            Team('Moss', 'MOSS'),
            Team('Ranheim TF', 'RAN'),
            Team('Raufoss', 'RAU'),
            Team('Sandnes Ulf', 'ULF'),
            Team('Sogndal', 'SOGN'),
            Team('Stabæk', 'STB'),
            Team('Start', 'STRT'),
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
    def update_team_csv(self):
        updated_something = False
        for team in self.teams:
            # find the row in standings for this teame
            team_standing = None
            for standing in self.standings:
                if team.name == standing[1] or team.name == standing[1].split(" ")[0]:  # team name is at index 1
                    team_standing = standing
                    break  # Exit loop once the matching team is found
            if team_standing is None:
                print(f"err. did not find team {team.name} in standings")
                return False
            
            team.n_played = int(team_standing[2]) 
            csv_n_played = self.reader.get_n_matches_played(team.name)
            if (team.n_played == csv_n_played): 
                if self.debug:
                    print(f"->already saved match {team.n_played} for {team.name}")
                continue # already saved last match played - continue

            self.reader.write_team_entry(team.name, team.n_played, team_standing[4], team_standing[3])
            updated_something = True
        return updated_something
    
    def compute_standings_after_full_round(self, round_number):
        # read historic data
        for team in self.teams:
            csv_entry = self.reader.get_team_entry(team.name, round_number)
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
    def update_csv_positions(self):
        n_registered_matches = self.reader.get_min_matches_played()
        n_registered_positions = self.reader.get_n_pos_rows_written()
        if n_registered_matches == n_registered_positions:
            return True
        if abs(n_registered_positions-n_registered_matches) > 1:
            print(f"WARN: registered matches is {n_registered_matches} but registered positions is only {n_registered_positions} ")
        
        # Compute positions for all rounds that havent gotten this
        for round_number in range(n_registered_positions+1, n_registered_matches+1):
            self.compute_standings_after_full_round(round_number)

        # Update "pos" column for each team
        for team in self.teams:
            self.reader.write_team_pos(team.name, round_number, team.match_history[round_number]['pos'])


    # compute the points_history for each contestant, using csv positions
    def compute_contestant_points_timeseries(self):
        # read csv file "POS" for i in range(n_min_played)
        n_pos_written = self.reader.get_n_pos_rows_written()
        for round_number in range(1, n_pos_written+1):
            round_standings = self.reader.get_simple_standings_at_round_number(round_number)
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

    def update_teams(self):
        did_update_teams = self.update_team_csv()



def main():
    debug = True
    ball = TippeData24(debug)

    print("\n  # Fetch standings")
    ball.fetch_standings()
    ball.print_standings()

    print("\n  # Update points of contestants")
    ball.update_current_points()
    ball.print_contestants()

    print("\n  # Update CSV with latest games")
    ball.update_team_csv()
    
    print("\n  # Get number of Pos Rows Written")
    ball.reader.get_n_pos_rows_written()

    print("\n  # Compute Standings After Full Round")
    ball.compute_standings_after_full_round(round_number=1)
    
    print("\n  # Update CSV positions")
    ball.update_csv_positions()

    print("\n  # Compute Contestant Timeseries")
    ball.compute_contestant_points_timeseries()

    
    

    
    n = ball.reader.get_min_matches_played()








if __name__ == "__main__":
    main()
