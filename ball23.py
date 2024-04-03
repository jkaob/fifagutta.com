import requests
from bs4 import BeautifulSoup
import csv
import common
from common import Team, CsvReader, Scraper, TippeData, Contestant

N_TEAMS = 16


class CsvReader23:
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


class Scraper23(Scraper):
    def __init__(self):
        super().__init__("https://www.eliteserien.no/tabell", 'data/2023.csv')

    def get_standings(self):
        r = requests.get(self.url)
        soup = BeautifulSoup(r.content, 'html.parser', from_encoding='utf-8')
        league_table = soup.find('table', class_="table--persist-area table table--league table--league-eliteserien")
        standings = []
        for tbody in league_table.find_all("tbody"):
            # ea row has all info we need
            # iterate over each team
            for row in tbody.find_all("tr", class_="table__row"):
                team_element = row.find("span", class_="table__typo--full")
                assert team_element is not None, "Expected to find team"
                name = team_element.string # team name

                td_elements = row.find_all("td") # get number data
                assert len(td_elements) == 11, f"Expected 11 elements, found  {len(td_elements)}"
                pos = int(td_elements[0].get_text())
                n_played = int(td_elements[2].get_text())
                goal_diff = int(td_elements[-3].get_text())
                n_points = int(td_elements[-2].get_text())
                # Append team status to current standings
                team = [pos, name, n_played, goal_diff, n_points]
                standings.append(team)
        return standings

    def get_team_history(self, team : Team):
        print("\n",team.name)
        r = requests.get(team.url)
        soup = BeautifulSoup(r.content, 'html.parser', from_encoding='utf-8')
        matches_table = soup.find('table', class_='table doubleScrollWrap__inner tablesorter customTableSorter')
        for tbody in matches_table.find_all("tbody"):
            # iterate over each row with no class (played matches)
            for row in tbody.find_all('tr', class_=""):
                td_elements = row.find_all("td") # each entry is a td_element
                # Check if it was in Eliteserien
                tournament = td_elements[8].get_text()
                if tournament != "Eliteserien":
                    continue
                # Check if team played home or away
                home_team = td_elements[4].get_text().split(" ")[0]
                away_team = td_elements[6].get_text().split(" ")[0]
                goals_str = td_elements[5].get_text()

                match_result = common.process_match_result(team.name, home_team, away_team, goals_str)
                if match_result is None:
                    continue  # Skip if match is live or hasn't started yet

                home_team, goals_str, away_team, result, goal_diff = match_result
                print(home_team, goals_str, away_team, result, "gd =", goal_diff)
                team.match_results.append(result)
                team.match_gd.append(goal_diff)


class TippeData23(TippeData):

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



data_dict = {
    'MrMaggyzinho': {
        'points': 0,  # total points
        'normalized': 0.0,
        'prediction': ['Bodø/Glimt', 'Brann', 'Molde', 'Lillestrøm', 'Rosenborg', 'Viking', 'Stabæk', 'Vålerenga', 'Sarpsborg', 'Odd', 'Strømsgodset', 'Tromsø', 'Sandefjord', 'Aalesund', 'Haugesund', 'HamKam'],
        'delta' : [0]*N_TEAMS,
        'points_history' : []  #how many points after each game played
    },
    'Gianni Infantino': {
        'points': 0,
        'normalized': 0.0,
        'prediction': ['Bodø/Glimt', 'Molde', 'Brann', 'Rosenborg', 'Lillestrøm', 'Vålerenga', 'Viking', 'Stabæk', 'Sarpsborg', 'Odd', 'Tromsø', 'Strømsgodset', 'Haugesund', 'HamKam', 'Sandefjord', 'Aalesund', ],
        'delta' : [0]*N_TEAMS,
        'points_history' : []
    },
    'ZaHaavi': {
        'points': 0,
        'normalized': 0.0,
        'prediction': ['Bodø/Glimt', 'Molde', 'Lillestrøm', 'Rosenborg', 'Viking', 'Brann', 'Sarpsborg', 'Vålerenga', 'Stabæk', 'Tromsø', 'Haugesund', 'Odd', 'Strømsgodset', 'Sandefjord', 'Aalesund', 'HamKam' ],
        'delta' : [0]*N_TEAMS,
        'points_history' : []
    },
    '#BjarmannUt': {
        'points': 0,
        'normalized': 0.0,
        'prediction':['Bodø/Glimt', 'Molde', 'Lillestrøm', 'Brann', 'Rosenborg', 'Viking', 'Vålerenga', 'Stabæk', 'Sarpsborg', 'Tromsø', 'Odd', 'Haugesund', 'Strømsgodset', 'Aalesund', 'Sandefjord', 'HamKam' ],
        'delta' : [0]*N_TEAMS,
        'points_history' : []
    },
    'Myra Craig': {
        'points': 0,
        'normalized': 0.0,
        'prediction': ['Molde', 'Bodø/Glimt', 'Lillestrøm', 'Rosenborg', 'Vålerenga', 'Brann', 'Sarpsborg', 'Stabæk', 'Viking', 'Odd', 'Tromsø', 'Strømsgodset', 'Aalesund', 'Haugesund', 'Sandefjord', 'HamKam' ],
        'delta' : [0]*N_TEAMS,
        'points_history' : []
    },
    'Jakob Haaland Dietz': {
        'points': 0,
        'normalized': 0.0,
        'prediction': ['Stabæk', 'Tromsø', 'Sarpsborg', 'Sandefjord', 'Strømsgodset', 'Bodø/Glimt', 'Viking', 'Odd', 'Brann', 'Rosenborg', 'Vålerenga', 'Molde', 'Haugesund', 'HamKam', 'Aalesund', 'Lillestrøm', ],
        'delta' : [0]*N_TEAMS,
        'points_history' : []
    },
    'Adrian/Sadrian': {
        'points': 0,
        'normalized': 0.0,
        'prediction': ['Bodø/Glimt', 'Brann', 'Molde', 'Rosenborg', 'Viking', 'Stabæk', 'Lillestrøm', 'Vålerenga', 'Odd', 'Aalesund', 'Sarpsborg', 'Strømsgodset', 'HamKam', 'Tromsø', 'Sandefjord', 'Haugesund', ],
        'delta' : [0]*N_TEAMS,
        'points_history' : []
    },
    'Joaquin Krave': {
        'points': 0,
        'normalized': 0.0,
        'prediction': ['Bodø/Glimt', 'Molde', 'Brann', 'Rosenborg', 'Lillestrøm', 'Vålerenga', 'Viking', 'Odd', 'Sarpsborg', 'Stabæk', 'Strømsgodset', 'HamKam', 'Tromsø', 'Aalesund', 'Haugesund', 'Sandefjord', ],
        'delta' : [0]*N_TEAMS,
        'points_history' : []
    },
    'Herman Ø (15)': {
        'points': 0,
        'normalized': 0.0,
        'prediction': ['Bodø/Glimt', 'Molde', 'Brann', 'Rosenborg', 'Lillestrøm', 'Viking', 'Vålerenga', 'Odd', 'Sarpsborg', 'Tromsø', 'Stabæk', 'HamKam', 'Strømsgodset', 'Haugesund', 'Aalesund', 'Sandefjord', ],
        'delta' : [0]*N_TEAMS,
        'points_history' : []
    },
}


teams = [
    Team('Stabæk', 'https://www.fotball.no/fotballdata/lag/kamper/?fiksId=269'),
    Team('Bodø/Glimt','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=4'),
    Team('Lillestrøm','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=177'),
    Team('Brann','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=298'),
    Team('Odd','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=270'),
    Team('Viking','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=198'),
    Team('Tromsø','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=2'),
    Team('Molde','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=3'),
    Team('Sandefjord','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=195'),
    Team('Sarpsborg','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=797'),
    Team('Vålerenga','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=169882'),
    Team('Rosenborg','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=145'),
    Team('HamKam','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=63'),
    Team('Haugesund','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=202'),
    Team('Strømsgodset','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=816'),
    Team('Aalesund','https://www.fotball.no/fotballdata/lag/kamper/?fiksId=15'),
]



def main():
    ball = TippeData()
    ball.fetch_standings()
    ball.update_dict()

    for name in ball.get_sorted_names():
        e = ball.data_dict[name]
        print(name,":", e['points'], f"[{e['normalized']:.2f}]")

    s = ball.get_sorted_dict()
    for e in s:
        print(e)



if __name__ == "__main__":
    main()
