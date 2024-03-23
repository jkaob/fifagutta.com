import csv

class Team:
    def __init__(self, team_name, url=""):
        self.name = team_name
        self.url = url
        self.match_results = [] #W,L,D for each match
        self.match_gd = [] #GD for each match
        self.cm_points = [] # cumulative
        self.cm_gd = []
        self.cm_pos = []
        self.n_played = 0

class Contestant:
    def __init__(self, name) -> None:
        self.name = name
        self.data = {
            'points': 0,  # total points
            'normalized': 0.0,
            'prediction': [],
            'delta' : [],
            'points_history' : []  #how many points after each game played
        }
    def set_prediction(self, prediction):
        self.data['prediction'] = prediction
        self.data['delta'] = [0] * len(prediction)


class Scraper:
    def __init__(self, url, csv) -> None:
        self.url = url
        self.csv = csv 
    
    def get_standings(self):
        pass 
    
    def get_team_history(self, team : Team):
        pass


class TippeData:

    def __init__(self, scraper, csvreader):
        self.scraper = scraper #Scraper()  # to get table
        self.reader = csvreader
        # Initialize dict with points computation
        
        # Initialize teams list with url to match history
        self.data_dict = {}
        self.teams = []
        self.csv = ""
        self.min_played = 0
        self.standings = []

    def set_data_dict(self, entries):
        self.data_dict = {}
        for name, value in entries.items():
            contestant = Contestant(name)
            contestant.set_prediction(value)
            self.data_dict[name] = contestant.data


    def fetch_standings(self):
        self.standings = self.scraper.get_standings()
        return self.standings

    def compute_points(self, name):
        prediction = self.data_dict[name]['prediction']
        total_points = 0
        print("standings: ", self.standings)
        for row in self.standings:
            team_name = row[1].split(" ")[0]
            team_ind = prediction.index(team_name) # index of team in prediction
            prediction_pos = team_ind+1 # table placement
            team_pos = row[0]
            points = abs(prediction_pos - team_pos)
            self.data_dict[name]['delta'][team_ind] = points # store points
            total_points += points
        self.data_dict[name]['points'] = total_points # store total points
        return total_points

    def update_dict(self):
        for name in self.data_dict:
            points = self.compute_points(name)
            self.data_dict[name]['points'] = points
        # Add normalized
        max_points = self.data_dict[max(self.data_dict, key=lambda x: self.data_dict[x]['points'])]['points']
        for name in self.data_dict:
            self.data_dict[name]['normalized'] = self.data_dict[name]['points'] / max_points

    def get_sorted_names(self):
        return sorted(self.data_dict.keys(), key=lambda x: self.data_dict[x]['points'])

    def get_sorted_dict(self):
        return dict(sorted(self.data_dict.items(), key=lambda x: x[1]['points'], reverse=False))


    def update(self):
        self.fetch_standings()
        self.update_dict()
        #self.update_teams()


    # Main history function
    def update_teams(self):
        # Find minimum number of matches played by everyone
        self.min_played = min(self.standings, key=lambda team: team[2])[2]
        # Check how many are saved in csv file
        csv_min_played = self.reader.get_min_matches_played()

        # See what work we must do
        # matches_to_add = self.min_played - csv_min_played
        # history = []
        # if (matches_to_add > 0):
        #     # Fetch online results
        #     for team in self.teams:
        #         self.scraper.get_team_history(team)
        #         self.update_team_history(team)
        #     history_csv = self.update_historic_standings()
        #     self.reader.update_csv(history_csv, matches_to_add, self.min_played)
        #     # rewrite history to compute format
        #     history = [[
        #         [i+1, j+1, history_csv[i][j][0], history_csv[i][j][1], history_csv[i][j][2]]
        #         for j in range(N_TEAMS)] for i in range(self.min_played)]

        # elif (matches_to_add < 0):
        #     assert(True), "err"
        # else: #compute using csv file
        #     history = self.reader.get_csv_history()
        history = self.reader.get_csv_history() #TODO: PLACEHOLDER FOR BUG. FIX THIS! 
        # Compute points using history
        self.compute_points_history(history)


    def compute_points_history(self, history):
        # for ea match
        for m in range(len(history)):
            match_standings = history[m]
            # for ea contestant
            for name in self.data_dict.keys():
                prediction = self.data_dict[name]['prediction']
                total_points = 0
                # for ea team: [Match number, Position, Team name, GD, Points]
                for row in match_standings:
                    team_name = row[2].split(" ")[0]
                    team_ind = prediction.index(team_name) # index of team in prediction
                    prediction_pos = team_ind+1 # table placement
                    team_pos = (int)(row[1])
                    points = abs(prediction_pos - team_pos)
                    total_points += points
                self.data_dict[name]['points_history'].append(total_points)


    def update_team_history(self, team):
        if len(team.cm_points) == len(team.match_results):
            return # already updated (probably)
        team.n_played = len(team.match_results)
        points = 0
        gd = 0
        for i in range(team.n_played):
            if (team.match_results[i] == "W"):
                points += 3
            elif (team.match_results[i] == "D"):
                points += 1
            gd += team.match_gd[i]
            team.cm_points.append(points)
            team.cm_gd.append(gd)


    def update_historic_standings(self):
        # Clear historic position
        for team in self.teams:
            team.cm_pos = []
        history = []
        # Basically create standings for each match played
        for i in range(self.min_played):
            standings = []
            for team in self.teams:
                info = (team.name, team.cm_gd[i], team.cm_points[i])
                standings.append(info)
            # Sort standings on points and GD
            standings.sort(key=lambda x: (x[2], x[1]), reverse=True)
            print(f"\nGame #{i+1}:\nPos |   Team    | GD | Points ")
            for i in range(len(standings)):
                print(i+1, standings[i])
                # Save historic position to the teams object
                team_name = standings[i][0]
                team_ref = next((team for team in self.teams if team.name == team_name), None) # find it
                team_ref.cm_pos.append(i+1)
            history.append(standings)
        print("row in history:", history[0][0])
        return history



class CsvReader:
    def __init__(self, filename : str, n_teams : int):
        self.csv = filename
        self.n_teams = n_teams

    def get_min_matches_played(self):
        # check if the current table is already saved
        with open(self.csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) <= 1:
                return 0
            # return number of matches played at end line
            return int(rows[-1][0])

    def get_csv_history(self):
        history = []
        with open(self.csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            min_played = (int)((len(rows)-1) / self.n_teams)
            for i in range(min_played):
                # Append [n_played, pos, team, gd, points]
                standings = rows[(1 + i*self.n_teams) : (1+self.n_teams + i*self.n_teams)]
                history.append(standings)
        print(f"Fetched {min_played} match(es) from file")
        return history

    def update_csv(self, history, n_matches_to_add, min_played):
        with open(self.csv, 'a',newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            for n in range(min_played-n_matches_to_add+1, min_played+1):
                print("Adding standings after match number ", n)
                standings = history[n-1]
                for j in range(len(standings)):
                    # Match number, Position, Team name, GD, Points
                    writer.writerow([n, j+1, standings[j][0], standings[j][1], standings[j][2]])
        print(f"Wrote {n_matches_to_add} match(es) to file")



# RANDOM FUNCTIONS

def process_match_result(self, team_name, home_team, away_team, goals_str):
    assert(team_name in [home_team, away_team]), "Cannot find team name in match"
    if goals_str == "-":
        return None  # Match is live or hasn't started yet

    goals = list(map(int, goals_str.split(" - ")))
    goal_diff = 0
    result = ""
    if team_name == home_team:
        goal_diff = goals[0] - goals[1]
    elif team_name == away_team:
        goal_diff = goals[1] - goals[0]

    if goals[0] > goals[1]:
        result = "W" if team_name == home_team else "L"
    elif goals[0] == goals[1]:
        result = "D"
    elif goals[0] < goals[1]:
        result = "W" if team_name == away_team else "L"

    return home_team, goals_str, away_team, result, goal_diff