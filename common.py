import csv

class Team:
    def __init__(self, team_name, team_short=""):
        self.name = team_name.split(" ")[0]  #  e.g. Sandnes
        self.name_full = team_name # e.g. Sandnes Ulf
        self.short = team_short  # Abbreviation (ULF)
        self.url = None
        self.match_results = [] # e.g. [W, D, L, D, ]
        self.match_gd = [] #GD for each match [+3, -2, -1]
        self.cm_points = [] # cumulative
        self.cm_gd = []
        self.cm_pos = []
        self.n_played = 0
        self.match_history = {}  #  match_data = {
            #     'points': csv_entry[2],
            #     'gd': csv_entry[3],
            #     'pos': None
            # }

class Contestant:
    def __init__(self, name, name_short="") -> None:
        self.name = name
        self.data = {
            'points': 0,  # total points
            'normalized': 0.0,
            'prediction': [],  # Team list in order
            #'short' : [],
            'delta' : [],  # for each team, how many penalty points
            'points_history' : [],  #how many points contestant had after each game played
        }
        self.short = name_short
        self.avatar = ""  # path to avatar #TODO

    def set_avatar(self, path):
        self.avatar = path

    def set_prediction(self, prediction):
        self.data['prediction'] = prediction
        self.data['delta'] = [0] * len(prediction)

    # def set_prediction_short(self, prediction_short):
    #     self.data['short'] = prediction_short

class Scraper:
    def __init__(self, url, csv) -> None:
        self.url = url
        self.csv = csv 
    
    def get_standings(self):
        pass 
    
    def get_team_history(self, team : Team):
        pass


class TippeData:

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
        self.csv = ""
        self.min_played = 0
        self.standings = []  # [ [pos, name, n_played, goal_diff, n_points] ]

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

    # def set_data_dict(self, entries):
    #     if not self.teams:
    #         print(f"teams not set! cant set data dict")
    #         return
        
    #     self.data_dict = {}
    #     for name, value in entries.items():
    #         contestant = Contestant(name)
    #         contestant.set_prediction(value)
    #         team_shorts = [self.get_team_short(team_name) for team_name in value]
    #         contestant.set_prediction_short(team_shorts)
    #         self.data_dict[name] = contestant.data

    def fetch_standings(self):
        self.standings = self.scraper.get_standings()
        return self.standings

    def compute_points(self, name):
        contestant = self.get_contestant(name)
        prediction = contestant.data['prediction']
        total_points = 0
        #print("standings: ", self.standings)
        for row in self.standings:
            team_name = row[1].split(" ")[0]
            # team_ind = prediction.index(team_name) 
            # index of team in prediction
            team_ind = next((index for index, obj in enumerate(prediction) \
                             if obj.name == team_name), None)
            prediction_pos = team_ind+1 # table placement
            team_pos = row[0]
            points = abs(prediction_pos - team_pos) # TODO - not use absolute here, but later 
            contestant.data['delta'][team_ind] = points # store points
            total_points += points
        contestant.data['points'] = total_points # store total points
        return total_points

    def update_current_points(self):
        for contestant in self.contestants:
            self.compute_points(contestant.name)
        # Add normalized points for visualization
        max_points = max(contestant.data['points'] for contestant in self.contestants)
        for contestant in self.contestants:
            contestant.data['normalized'] = contestant.data['points'] / max_points


    def get_sorted_contestants(self):
        sorted_contestants = sorted(self.contestants, key=lambda contestant: contestant.data['points'])
        return sorted_contestants
        # Create a dictionary with contestant names as keys and their data as values, sorted by 'points'
        #return {contestant.name: contestant.data for contestant in sorted(self.contestants, key=lambda contestant: contestant.data['points'])}
    
    def get_sorted_names(self):
        # Sort the contestants based on 'points' and return their names
        return [contestant.name for contestant in self.get_sorted_contestants()]


    # MAIN FCN - DO THIS ONLINE
    def update(self):
        self.fetch_standings()
        self.update_current_points()
        self.update_teams_history() # TODO
        #self.update_teams()


    # Main history function TODO 
    def update_teams(self):
        # Find minimum number of matches played by everyone
        self.min_played = min(self.standings, key=lambda team: team[2])[2]
        # Check how many are saved in csv file
        csv_min_played = self.reader.get_min_matches_played()
        #     history = self.reader.get_csv_history()
        history = self.reader.get_csv_history() #TODO: PLACEHOLDER FOR BUG. FIX THIS! 
        # Compute points using history
        self.compute_points_history(history)


    def compute_points_history(self, history):
        # for ea match
        for m in range(len(history)):
            match_standings = history[m]
            # for ea contestant
            for contestant in self.contestants:
                prediction = contestant.data['prediction']
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
    
    def print_standings(self):
        print("POS,TEAM,PLAYED,GD,POINTS")
        for r in self.standings:
            print(r)
        print("-------------------------")

    def print_contestants(self):
        print("---Current leaderboard---")
        for c in self.get_sorted_contestants():
            print(f"{c.name}: {c.data['points']} points")
        print("-------------------------")




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