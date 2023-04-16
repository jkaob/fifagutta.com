import requests
from bs4 import BeautifulSoup

class Scraper:
    def __init__(self):
        self.url = "https://www.eliteserien.no/tabell"

    def get_standings(self):
        r = requests.get(self.url)
        soup = BeautifulSoup(r.content, 'html.parser', from_encoding='utf-8')
        league_table = soup.find('table', class_="table--persist-area table table--league table--league-eliteserien")
        standings = []
        for tbody in league_table.find_all("tbody"):
            # ea row has all info we need
            for row in tbody.find_all("tr", class_="table__row"):
                team_element = row.find("span", class_="table__typo--full")
                assert team_element is not None, "Expected to find team"
                name = team_element.string

                td_elements = row.find_all("td") # get number data
                assert len(td_elements) == 11, f"Expected 11 elements, found  {len(td_elements)}"
                pos = int(td_elements[0].get_text())
                n_played = int(td_elements[2].get_text())
                n_goal_diff = int(td_elements[-3].get_text())
                n_points = int(td_elements[-2].get_text())
                team = [pos, name, n_played, n_goal_diff, n_points]
                standings.append(team)
        return standings


class TippeData:
    def __init__(self):
        self.scraper = Scraper()  # to get table
        self.data_dict = {
            'MrMaggyzinho': {
                'points': 0,  # total points
                'normalized': 0.0,
                'prediction': ['Bodø/Glimt', 'Brann', 'Molde', 'Lillestrøm', 'Rosenborg', 'Viking', 'Stabæk', 'Vålerenga', 'Sarpsborg', 'Odd', 'Strømsgodset', 'Tromsø', 'Sandefjord', 'Aalesund', 'Haugesund', 'HamKam'],
                'delta' : [0]*16,  # penalty points per team
            },
            'Gianni Infantino': {
                'points': 0,
                'normalized': 0.0,
                'prediction': ['Bodø/Glimt', 'Molde', 'Brann', 'Rosenborg', 'Lillestrøm', 'Vålerenga', 'Viking', 'Stabæk', 'Sarpsborg', 'Odd', 'Tromsø', 'Strømsgodset', 'Haugesund', 'HamKam', 'Sandefjord', 'Aalesund', ],
                'delta' : [0]*16,
            },
            'ZaHaavi': {
                'points': 0,
                'normalized': 0.0,
                'prediction': ['Bodø/Glimt', 'Molde', 'Lillestrøm', 'Rosenborg', 'Viking', 'Brann', 'Sarpsborg', 'Vålerenga', 'Stabæk', 'Tromsø', 'Haugesund', 'Odd', 'Strømsgodset', 'Sandefjord', 'Aalesund', 'HamKam' ],
                'delta' : [0]*16,
            },
            '#BjarmannUt': {
                'points': 0,
                'normalized': 0.0,
                'prediction':['Bodø/Glimt', 'Molde', 'Lillestrøm', 'Brann', 'Rosenborg', 'Viking', 'Vålerenga', 'Stabæk', 'Sarpsborg', 'Tromsø', 'Odd', 'Haugesund', 'Strømsgodset', 'Aalesund', 'Sandefjord', 'HamKam' ],
                'delta' : [0]*16,
            },
            'Myra Craig': {
                'points': 0,
                'normalized': 0.0,
                'prediction': ['Molde', 'Bodø/Glimt', 'Lillestrøm', 'Rosenborg', 'Vålerenga', 'Brann', 'Sarpsborg', 'Stabæk', 'Viking', 'Odd', 'Tromsø', 'Strømsgodset', 'Aalesund', 'Haugesund', 'Sandefjord', 'HamKam' ],
                'delta' : [0]*16,
            },
            'Jakob Haaland Dietz': {
                'points': 0,
                'normalized': 0.0,
                'prediction': ['Stabæk', 'Tromsø', 'Sarpsborg', 'Sandefjord', 'Strømsgodset', 'Bodø/Glimt', 'Viking', 'Odd', 'Brann', 'Rosenborg', 'Vålerenga', 'Molde', 'Haugesund', 'HamKam', 'Aalesund', 'Lillestrøm', ],
                'delta' : [0]*16,
            },
            'Adrian/Sadrian': {
                'points': 0,
                'normalized': 0.0,
                'prediction': ['Bodø/Glimt', 'Brann', 'Molde', 'Rosenborg', 'Viking', 'Stabæk', 'Lillestrøm', 'Vålerenga', 'Odd', 'Aalesund', 'Sarpsborg', 'Strømsgodset', 'HamKam', 'Tromsø', 'Sandefjord', 'Haugesund', ],
                'delta' : [0]*16,
            },
            'Joaquin Krave': {
                'points': 0,
                'normalized': 0.0,
                'prediction': ['Bodø/Glimt', 'Molde', 'Brann', 'Rosenborg', 'Lillestrøm', 'Vålerenga', 'Viking', 'Odd', 'Sarpsborg', 'Stabæk', 'Strømsgodset', 'HamKam', 'Tromsø', 'Aalesund', 'Haugesund', 'Sandefjord', ],
                'delta' : [0]*16,
            },
            'Herman Ø (15)': {
                'points': 0,
                'normalized': 0.0,
                'prediction': ['Bodø/Glimt', 'Molde', 'Brann', 'Rosenborg', 'Lillestrøm', 'Viking', 'Vålerenga', 'Odd', 'Sarpsborg', 'Tromsø', 'Stabæk', 'HamKam', 'Strømsgodset', 'Haugesund', 'Aalesund', 'Sandefjord', ],
                'delta' : [0]*16,
            },
        }

    def fetch_standings(self):
        self.standings = self.scraper.get_standings()
        return self.standings

    def compute_points(self, name):
        prediction = self.data_dict[name]['prediction']
        total_points = 0
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
