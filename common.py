import csv
from bs4 import BeautifulSoup
import requests

class Team:
    def __init__(self, team_name, team_short=""):
        self.name = team_name.split(" ")[0]  #  e.g. Sandnes
        self.name_full = team_name # e.g. Sandnes Ulf
        self.short = team_short  # Abbreviation (ULF)
        #self.match_results = [] # e.g. [W, D, L, D, ]
        #self.match_gd = [] #GD for each match [+3, -2, -1]
        #self.cm_points = [] # cumulative
        #self.cm_gd = []
        #self.cm_pos = []
        #self.n_played = 0
        self.match_history = {} # {key= match_number . Value= {
                                #     'points': int,
                                #     'gd': int,
                                #     'pos': int
                                # }
        self.avg_placement = 0
    def to_dict(self):
        return {
            'name': self.name,
            'name_full': self.name_full,
            'short': self.short,
            # Include other necessary attributes
        }


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
            'corrects' : []  # bool : True if prediction is correct
        }
        self.short = name_short
        self.avatar = ""  # path to avatar #TODO

    def set_avatar(self, path):
        self.avatar = path

    def set_prediction(self, prediction):
        self.data['prediction'] = prediction
        self.data['delta'] = [0] * len(prediction)
        self.data['corrects'] = [False] * len(prediction)

    def to_dict(self):
        #print("points history length: ", len(self.data['points_history']))
        return {
            'name': self.name,
            'data': {
                'points': self.data['points'],
                'normalized': self.data['normalized'],
                'prediction': [team.to_dict() for team in self.data['prediction']],
                'delta': self.data['delta'],
                'points_history': self.data['points_history'],
                # Include other necessary attributes
            },
            'short': self.short,
            'avatar': self.avatar,
            # Include other necessary attributes
        }



class Scraper():
    def __init__(self, year) -> None:
        self.year = year
        self.url = 'https://www.obos-ligaen.no/resultater'
        self.csv = f'data/{year}.csv'

    def get_team_history(self, team : Team):
        pass

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
