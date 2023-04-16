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
        self.data_dict = {
            'MrMaggyzinho': {
                'points': 0,
                'normalized': 0.0,
                'guess': ['Bodø/Glimt', 'Brann', 'Molde', 'Lillestrøm', 'Rosenborg', 'Viking', 'Stabæk', 'Vålerenga', 'Sarpsborg', 'Odd', 'Strømsgodset', 'Tromsø', 'Sandefjord', 'Aalesund', 'Haugesund', 'HamKam'],
            },
            'Gianni Infantino': {
                'points': 0,
                'normalized': 0.0,
                'guess': ['Bodø/Glimt', 'Molde', 'Brann', 'Rosenborg', 'Lillestrøm', 'Vålerenga', 'Viking', 'Stabæk', 'Sarpsborg', 'Odd', 'Tromsø', 'Strømsgodset', 'Haugesund', 'HamKam', 'Sandefjord', 'Aalesund', ],
            },
            'ZaHaavi': {
                'points': 0,
                'normalized': 0.0,
                'guess': ['Bodø/Glimt', 'Molde', 'Lillestrøm', 'Rosenborg', 'Viking', 'Brann', 'Sarpsborg', 'Vålerenga', 'Stabæk', 'Tromsø', 'Haugesund', 'Odd', 'Strømsgodset', 'Sandefjord', 'Aalesund', 'HamKam' ],
            },
            '#BjarmannUt': {
                'points': 0,
                'normalized': 0.0,
                'guess':['Bodø/Glimt', 'Molde', 'Lillestrøm', 'Brann', 'Rosenborg', 'Viking', 'Vålerenga', 'Stabæk', 'Sarpsborg', 'Tromsø', 'Odd', 'Haugesund', 'Strømsgodset', 'Aalesund', 'Sandefjord', 'HamKam' ],
            },
            'Myra Craig': {
                'points': 0,
                'normalized': 0.0,
                'guess': ['Molde', 'Bodø/Glimt', 'Lillestrøm', 'Rosenborg', 'Vålerenga', 'Brann', 'Sarpsborg', 'Stabæk', 'Viking', 'Odd', 'Tromsø', 'Strømsgodset', 'Aalesund', 'Haugesund', 'Sandefjord', 'HamKam' ],
            },
            'Jakob Haaland Dietz': {
                'points': 0,
                'normalized': 0.0,
                'guess': ['Stabæk', 'Tromsø', 'Sarpsborg', 'Sandefjord', 'Strømsgodset', 'Bodø/Glimt', 'Viking', 'Odd', 'Brann', 'Rosenborg', 'Vålerenga', 'Molde', 'Haugesund', 'HamKam', 'Aalesund', 'Lillestrøm', ],
            },
            'Adrian/Sadrian': {
                'points': 0,
                'normalized': 0.0,
                'guess': ['Bodø/Glimt', 'Brann', 'Molde', 'Rosenborg', 'Viking', 'Stabæk', 'Lillestrøm', 'Vålerenga', 'Odd', 'Aalesund', 'Sarpsborg', 'Strømsgodset', 'HamKam', 'Tromsø', 'Sandefjord', 'Haugesund', ],
            },
            'Joaquin Krave': {
                'points': 0,
                'normalized': 0.0,
                'guess': ['Bodø/Glimt', 'Molde', 'Brann', 'Rosenborg', 'Lillestrøm', 'Vålerenga', 'Viking', 'Odd', 'Sarpsborg', 'Stabæk', 'Strømsgodset', 'HamKam', 'Tromsø', 'Aalesund', 'Haugesund', 'Sandefjord', ],
            },
            'Herman Ø (15)': {
                'points': 0,
                'normalized': 0.0,
                'guess': ['Bodø/Glimt', 'Molde', 'Brann', 'Rosenborg', 'Lillestrøm', 'Viking', 'Vålerenga', 'Odd', 'Sarpsborg', 'Tromsø', 'Stabæk', 'HamKam', 'Strømsgodset', 'Haugesund', 'Aalesund', 'Sandefjord', ],
            },
        }
        self.scraper = Scraper()
        self.standings = self.scraper.get_standings()

    def fetch_standings(self):
        self.standings = self.scraper.get_standings()
        return self.standings

    def compute_points(self, guess):
        points = 0
        for row in self.standings:
            team_short = row[1].split(" ")[0]
            guess_pos = guess.index(team_short)+1
            team_pos = row[0]
            p = abs(guess_pos - team_pos)
            points += p
        return points

    def update_dict(self):
        for name in self.data_dict:
            points = self.compute_points(self.data_dict[name]['guess'])
            self.data_dict[name]['points'] = points
        # Add normalized
        max_points = self.data_dict[max(self.data_dict, key=lambda x: self.data_dict[x]['points'])]['points']
        for name in self.data_dict:
            self.data_dict[name]['normalized'] = self.data_dict[name]['points'] / max_points

    def get_sorted_names(self):
        return sorted(self.data_dict.keys(), key=lambda x: self.data_dict[x]['points'])

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




if __name__ == "__main__":
    main()
