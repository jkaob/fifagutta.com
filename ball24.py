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


class CsvReader24():
    def __init__(self, filename: str, teams):
        self.csv = filename
        self.team_names = [t.name for t in teams]
        self.n_teams = len(self.team_names)

    # n_matches for a specific team
    def get_n_matches_played(self, team_name):
        n_matches_played = 0
        with open(self.csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                if row[0] == team_name and row[2] != '-':
                    n_matches_played += 1
        return n_matches_played
    
    def get_min_matches_played(self):
        n_min = 2*(self.n_teams-1)
        for name in self.team_names:
            n_played = self.get_n_matches_played(name)
            n_min = min(n_min, n_played)
        print(f"all teams have played at least {n_min} rounds")
        return n_min
    
    def add_team_entry(self, team_name, round_number, new_points, new_gd):
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
        print(f"added round {round_number} for {team_name}")

    # updates the "pos" column of a team
    def update_team_pos(self, team_name, round_number, new_position):
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
        print(f"updated position at round {round_number} for {team_name}")
        return True


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
        super().__init__()
        self.teams = [
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
            Team('Stabæk', 'STB'),
            Team('Start', 'STR'),
            Team('Vålerenga', 'VIF'),
            Team('Åsane', 'ÅSA'),
        ]
        self.reader = CsvReader24("data/2024.csv", self.teams)
        self.scraper = Scraper24()

        entries = data.tips24.ENTRIES
        self.set_data_dict(entries)


    def update_team_csv(self):
        updated_something = False
        for team in self.teams:
            # find the row in standings for this teame
            team_standing = None
            for standing in self.standings:
                if standing[1] == team.name:  # team name is at index 1
                    team_standing = standing
                    break  # Exit loop once the matching team is found
            if team_standing is None:
                print(f"err. did not find team {team.name} in standings")
                return False
            
            team.n_played = team_standing[2] 
            csv_n_played = self.reader.get_n_matches_played(team.name)
            if (team.n_played == csv_n_played): 
                continue # already saved last match played - continue
            self.reader.add_team_entry(team.name, team.n_played, team_standing[4], team_standing[3])
            updated_something = True
        return updated_something

    def update_teams(self):
        self.update_team_csv()


def main():
    ball = TippeData24()
    ball.fetch_standings()
    ball.update_dict()

    ball.print_standings()

    n = ball.reader.get_min_matches_played()

    for name in ball.get_sorted_names():
        e = ball.data_dict[name]
        print(name,":", e['points'], f"[{e['normalized']:.2f}]")

    s = ball.get_sorted_dict()








if __name__ == "__main__":
    main()
