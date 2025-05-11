from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
from .common import Team, Contestant

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

                assert (len(td_elements) == 11 or len(td_elements) == 10), f"Expected 10 or 11 elements, found  {len(td_elements)}"
                
                j = 0 if (len(td_elements) == 10) else 1 # offset for whenever they decide to change the table format 
                
                pos = int(td_elements[0].get_text())
                n_played = int(td_elements[2].get_text())
                goal_diff = int(td_elements[-(2+j)].get_text())
                n_points = int(td_elements[-(1+j)].get_text())
                # Append team status to current standings
                team = [pos, name, n_played, goal_diff, n_points]
                standings.append(team)
        return standings



class ScheduleScraper():
    def __init__(self) -> None:
        self.url_schedule = 'https://www.obos-ligaen.no/terminliste'
        self.url_results = 'https://www.obos-ligaen.no/resultater'


    # get all elements that are scheduled to be played in the next 1-n days
    def get_next_match_elements(self, n_days=7, n_min_hours=0.25, verbose=False):
        now = datetime.now()
        in_n_hours = now + timedelta(minutes=n_min_hours*60)
        in_n_days = datetime.today() + timedelta(days=n_days)

        r = requests.get(self.url_schedule)
        soup = BeautifulSoup(r.content, 'html.parser', from_encoding='utf-8')
        next_matches = []  # {home_team, away_team, date_time, round_number}
        schedule_tab = soup.find('table', class_="schedule__table")
        
        for row in schedule_tab.find_all('tr'):
            
            date_td = row.find('td', class_='schedule__match__item--date')
            teams_td = row.find('td', class_='schedule__match__item--teams')
            round_td = row.find('td', class_='schedule__match__item--round')
            if not date_td or not teams_td or not round_td:
                continue

            # get date string
            date_span = date_td.find('span')
            time_span = date_td.find('span', class_='schedule__time')
            if not date_span or not time_span:
                continue
            
            # parse date
            date_str = date_span.text.strip().replace('.', '').strip()
            time_str = time_span.text.strip()
            try:
                match_datetime = datetime.strptime(f"{date_str} {time_str}", '%d%m%Y %H:%M')
            except ValueError:
                print(f"Error parsing datetime: {date_str} {time_str}")
                continue

            if in_n_hours <= match_datetime <= in_n_days:
                teams_text = teams_td.get_text(separator=' ').strip()
                home_team = teams_text.split('-')[0].strip()
                away_team_span = teams_td.find('span', class_='schedule__team--opponent')
                away_team = away_team_span.text.strip() if away_team_span else "?"

                round_number_span = round_td.find('span')
                round_number = round_number_span.text.strip() if round_number_span else "?"

                datetime_str = match_datetime.strftime('%d.%m.%Y %H:%M')

                next_matches.append({
                    'round_number': round_number,
                    'date_time': datetime_str,
                    'home_team': home_team,
                    'away_team': away_team,
                })

            elif match_datetime > in_n_days:
                # stop looping once we’re past range
                break

        if verbose:
            for match in next_matches:
                print(f"{match['home_team']} vs {match['away_team']} on {match['date_time']} (Round: {match['round_number']})")


        return next_matches
                
    def print_next_matches(self, n_days=7):
        next_matches = self.get_next_match_elements(n_days, 0.25)
        for match in next_matches:
            print(f"{match['home_team']} vs {match['away_team']} on {match['date_time']} (Round: {match['round_number']})")
            

    def get_past_match_elements(self, verbose=False):
        r = requests.get(self.url_results)
        soup = BeautifulSoup(r.content, 'html.parser', from_encoding='utf-8')
        past_matches = []
        results_tab = soup.find('table', class_='schedule__table')

        for row in results_tab.find_all('tr'):

            date_td = row.find('td', class_='schedule__match__item--date')
            teams_td = row.find('td', class_='schedule__match__item--teams')
            round_td = row.find('td', class_='schedule__match__item--round')
            result_td = row.find('td', class_='schedule__match__item--result')
        
            if not date_td or not teams_td or not round_td or not result_td:
                continue

            date_str = date_td.text.split()[0]  
            parts = date_td.text.strip().split()
            time_str = parts[1] if len(parts) > 1 else ''
            
            try:
                match_datetime = datetime.strptime(f"{date_str} {time_str}", '%d.%m.%Y %H:%M')
            except ValueError:
                print(f"Error parsing datetime: {date_str} {time_str}")
                continue

            
            teams_text = teams_td.get_text(separator=' ').strip()
            home_team = teams_text.split('-')[0].strip()
            away_team_span = teams_td.find('span', class_='results__team--opponent')
            away_team = away_team_span.text.strip() if away_team_span else "?"

            round_number_span = round_td.find('span')
            round_number = round_number_span.text.strip() if round_number_span else "?"

            datetime_str = match_datetime.strftime('%d.%m.%Y %H:%M')

            past_matches.append({
                'round_number': round_number,
                'date_time':  datetime_str,
                'home_team':  home_team,
                'away_team':  away_team,
                'home_goals': result_td.text.split('-')[0].strip(),
                'away_goals': result_td.text.split('-')[1].strip(),
            })

        if verbose:
            for match in past_matches:
                print(f"({match['round_number']}) {match['home_team']} ({match['home_goals']})  vs ({match['away_goals']}) {match['away_team']} on {match['date_time']} ")

        return past_matches

    def print_past_matches(self):
        past_matches = self.get_all_past_matches()
        for match in past_matches:
            print(f"({match['round_number']}) {match['home_team']} ({match['home_goals']})  vs ({match['away_goals']}) {match['away_team']} on {match['date_time']}")
