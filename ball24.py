import requests
from bs4 import BeautifulSoup
import csv
import data.tips24
from common import TippeData, Scraper, Team, CsvReader, Contestant

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
                assert len(td_elements) == 10, f"Expected 10 elements, found  {len(td_elements)}"
                pos = int(td_elements[0].get_text())
                n_played = int(td_elements[2].get_text())
                goal_diff = int(td_elements[-2].get_text())
                n_points = int(td_elements[-1].get_text())
                # Append team status to current standings
                team = [pos, name, n_played, goal_diff, n_points]
                standings.append(team)
        return standings


class TippeData24(TippeData):
    def __init__(self):
        scraper = Scraper24()
        super().__init__(scraper, CsvReader('data/2024.csv', 16))
        self.teams = [
            Team('Aalesund'),
            Team('Bryne'),
            Team('Egersund'),
            Team('Kongsvinger'),
            Team('Levanger'),
            Team('Lyn'),
            Team('Mjøndalen'),
            Team('Moss'),
            Team('Ranheim TF'),
            Team('Raufoss'),
            Team('Sandnes Ulf'),
            Team('Sogndal'),
            Team('Stabæk'),
            Team('Start'),
            Team('Vålerenga'),
            Team('Åsane'),
        ]
        entries = data.tips24.ENTRIES
        self.set_data_dict(entries)



def main():
    ball = TippeData24()
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
