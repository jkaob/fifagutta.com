import requests
from bs4 import BeautifulSoup
import csv
import common
from common import Team, CsvReader, Scraper

N_TEAMS = 16



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
