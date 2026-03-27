import json
import os
from pprint import pformat

def generate_files_from_tips_json(year=2026):
    """
    Reads cache/tips{year}.json and generates:
    - cache/emails.txt: list of email addresses (one per line)
    - cache/tips{year}.py: Python dict ENTRIES with player predictions
    """
    json_path = f"cache/tips{year}.json"
    tips_py_path = f"cache/tips{year}.py"
    emails_path = "cache/emails.txt"
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Extract emails
    emails = [player_data.get("email", "") for player_data in data.values() if player_data.get("email")]
    
    # Prepare ENTRIES dict (remove email from entries)
    entries = {}
    for player_id, player_data in data.items():
        entries[player_id] = {
            "name": player_data.get("name", ""),
            "short": player_data.get("short", ""),
            "prediction": player_data.get("prediction", [])
        }
    
    with open(emails_path, "w", encoding="utf-8") as f:
        for email in emails:
            f.write(email + "\n")
    
    with open(tips_py_path, "w", encoding="utf-8") as f:
        f.write("ENTRIES = ")
        f.write(pformat(entries, indent=4, width=120))
        f.write("\n")
    
    print(f"Generated {emails_path} and {tips_py_path}")



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
