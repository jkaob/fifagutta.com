# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

url="https://www.eliteserien.no/tabell"

r = requests.get(url)
soup = BeautifulSoup(r.text, 'html.parser')

league_table = soup.find('table', class_="table--persist-area table table--league table--league-eliteserien")

standings = []

for tbody in league_table.find_all("tbody"):
    # ea row has all info we need
    for row in tbody.find_all("tr", class_="table__row"):
        team_element = row.find("span", class_="table__typo--full")
        if team_element is None:
            break
        name = team_element.string
        # get points
        td_elements = row.find_all("td")
        
