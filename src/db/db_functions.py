### 
# CRUD functions for database models, and other helper functions related to the database.
###

from typing import List
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta

from . import db
from .models import Player, Bet, Match, Kampspill26
from ..scraper import ScheduleScraper

def add_bet_to_db(db, user_id, match_id, goals_home, goals_away, commit=True):
    bet = Bet.query.filter_by(player_id=user_id, match_id=match_id).first()
    if not bet:
        bet = Bet(
            player_id=user_id, match_id=match_id, goals_home=goals_home, goals_away=goals_away)
        db.session.add(bet)
        print(f"Added bet (ID {bet.id}:  {bet.goals_home} - {bet.goals_away})")
    else:
        bet.goals_home = goals_home
        bet.goals_away = goals_away
        print(f"Updated bet (ID {bet.id}:  {bet.goals_home} - {bet.goals_away})")
    
    if commit:
        db.session.commit()
    return bet

### 2026 updated functions:

# Get upcoming matches from db
def get_upcoming_matches(start: datetime, end: datetime, n_max: int = 50):
    """
    Returns a list of upcoming Match objects within the date range, limited to n_max.
    """
    matches = Match.query.filter(
        Match.play_date >= start,
        Match.play_date <= end
    ).order_by(Match.play_date).limit(n_max).all()
    return matches

# Get past matches with results from db
def get_finished_matches():
    """
    Returns a list of past Match objects that have results.
    """
    from ..app_globals import YEAR
    year_start = datetime(YEAR, 1, 1)
    year_end = datetime(YEAR, 12, 31)
    
    past_matches = Match.query.filter(
        Match.home_goals.isnot(None),
        Match.away_goals.isnot(None),
        Match.play_date >= year_start,
        Match.play_date <= year_end
    ).order_by(Match.play_date.desc()).all()
    return past_matches

# Get bets for a user_id for a list of matches
def get_user_bets_for_matches(user_id: int, match_ids: List[int]):
    """
    Returns a dict {match_id: Bet} for the user's bets on the specified matches.
    """
    bets = Bet.query.filter(
        Bet.player_id == user_id,
        Bet.match_id.in_(match_ids)
    ).all()
    user_bets = {bet.match_id: bet for bet in bets}
    return user_bets

# Player Score table
def get_player_scores():
    """
    Returns a list of dicts, one per player, with their scores.
    """
    players = Player.query.all()
    scores = []
    for p in players:
        score_entry = Kampspill26.query.filter_by(player_id=p.id).first()
        if score_entry:
            scores.append({
                'username': p.username,
                'username_short': p.username_short,
                'num_points': score_entry.num_points,
                'num_bets': score_entry.num_bets,
                'num_corrects': score_entry.num_corrects,
                'num_hub': score_entry.num_hub
            })
    return sorted(scores, key=lambda x: x['num_points'], reverse=True)

# Update player scores in table using prev match results
def update_player_scores():
    """
    Computes and updates player scores in the Kampspill26 table based on finished matches and bets.
    This replaces the compute_scores() logic but uses DB queries for efficiency.
    """
    
    # Get all finished matches
    finished_matches = get_finished_matches()
    if not finished_matches:
        return  # No matches to process
    
    match_ids = [m.id for m in finished_matches]
    
    all_bets = Bet.query.filter(Bet.match_id.in_(match_ids)).all()

    # Group bets by match_id for easier access
    bets_by_match = {}
    for bet in all_bets:
        if bet.match_id not in bets_by_match:
            bets_by_match[bet.match_id] = []
        bets_by_match[bet.match_id].append(bet)

    
    # Accumulate scores per player
    player_scores = {}

    for match in finished_matches:
        match_bets = bets_by_match.get(match.id, [])
        for bet in match_bets:
            player_id = bet.player_id
            if player_id not in player_scores:
                player_scores[player_id] = {
                    'num_points': 0,
                    'num_bets': 0,
                    'num_corrects': 0,
                    'num_hub': 0 
                }
            ps = player_scores[player_id]
            ps['num_bets'] += 1
            
            # Check exact score
            if bet.goals_home == match.home_goals and bet.goals_away == match.away_goals:
                ps['num_corrects'] += 1
                ps['num_points'] += 2
            # Check correct outcome
            elif ((bet.goals_home > bet.goals_away and match.home_goals > match.away_goals) or
                  (bet.goals_home < bet.goals_away and match.home_goals < match.away_goals) or
                  (bet.goals_home == bet.goals_away and match.home_goals == match.away_goals)):
                ps['num_hub'] += 1
                ps['num_points'] += 1
    
    # Now update the Kampspill26 table
    for player_id, scores in player_scores.items():
        # Upsert: update if exists, else create
        score_entry = Kampspill26.query.filter_by(player_id=player_id).first()
        if not score_entry:
            score_entry = Kampspill26(player_id=player_id, **scores)
            db.session.add(score_entry)
        else:
            score_entry.num_points = scores['num_points']
            score_entry.num_bets = scores['num_bets']
            score_entry.num_corrects = scores['num_corrects']
            score_entry.num_hub = scores['num_hub']
    
    try:
        db.session.commit()
        print("Player scores updated successfully.")
    except IntegrityError:
        db.session.rollback()
        print("Error updating player scores.")


## Functions to add and update matches in DB

def add_matches_to_db(n_next_days=7, n_min_hours=0.25, verbose=False):
    scraper = ScheduleScraper()
    raw_next = scraper.get_next_match_elements(n_next_days, n_min_hours, verbose)
    raw_past = scraper.get_past_match_elements(verbose)

    next_matches = ensure_matches_in_db(raw_next)
    past_matches = ensure_past_matches_in_db(raw_past)
    pass


def ensure_matches_in_db(next_matches):
    """
    next_matches is a list of dicts. 
    This will insert any that dont exist yet, and return a list of Match objects.
    """
    db_matches = []

    for m in next_matches:
        # parse the datetime back into a Python datetime
        play_date = datetime.strptime(m['date_time'], '%d.%m.%Y %H:%M')

        # try to fetch existing
        match_obj = (
          Match.query.filter_by(
                home_team=m['home_team'],
                away_team=m['away_team']
            ).first()
        )

        if not match_obj:
            # doesn’t exist → create it
            match_obj = Match(
              home_team    = m['home_team'],
              away_team    = m['away_team'],
              play_date    = play_date,
              round_number = int(m['round_number'].lstrip('#'))
            )
            db.session.add(match_obj)
            try:
                db.session.commit()
                print("Add match ID ", match_obj.id)   #  here you already have the new integer ID
            except IntegrityError:
                db.session.rollback()
                # another process inserted it in the meantime
                match_obj = Match.query.filter_by(
                    home_team=m['home_team'],
                    away_team=m['away_team']
                ).first()
        # if object exists:
        else:
            if match_obj.play_date != play_date:
                print("Update match ID date", match_obj.id)
                match_obj.play_date = play_date
                db.session.commit()
        db_matches.append(match_obj)
    return db_matches


def ensure_past_matches_in_db(past_matches):
    """
    past_matches is a list of dicts.
    This will insert any that don't exist yet, or update home_goals/away_goals,
    and return a list of Match objects.
    """
    db_matches = []

    for m in past_matches:
        play_date = datetime.strptime(m['date_time'], '%d.%m.%Y %H:%M')

        match_obj = (
            Match.query.filter_by(
                home_team=m['home_team'],
                away_team=m['away_team']
            ).first()
        )

        if not match_obj:
            # create new match
            match_obj = Match(
                home_team=m['home_team'],
                away_team=m['away_team'],
                play_date=play_date,
                round_number=int(m['round_number'].lstrip('#')),
                home_goals=m['home_goals'],
                away_goals=m['away_goals']
            )
            print("Added match ID", match_obj.id)
            db.session.add(match_obj)
        else:
            # update results if they are not set
            if (match_obj.home_goals is None and match_obj.away_goals is None):
                print("Updating match ID goals", match_obj.id)
            match_obj.home_goals = m['home_goals']
            match_obj.away_goals = m['away_goals']

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            print("Conflict on match:", m['home_team'], m['away_team'])

        db_matches.append(match_obj)

    return db_matches



# Get league predicitons for all players, formatted as a dict { player_id: { name, short, prediction: [team1, team2, ...] } }
def get_latest_predictions_formatted():
    """
    Fetches all players and their latest table tips predictions from the database
    """
    from .models import Tabelltips26
    
    entries = {}
    players = Player.query.all()
    
    for player in players:
        # Get all predictions for this player, sorted by rank
        predictions = Tabelltips26.query.filter_by(player_id=player.id).order_by(Tabelltips26.rank).all()
        
        # Extract team names in order
        team_list = [pred.team_name for pred in predictions]
        
        # Build the entry
        entries[str(player.id)] = {
            "full_name": player.full_name,
            "name" : player.username,
            "short": player.username_short or "",
            "prediction": team_list,
            "email": player.email or ""
        }
    
    return entries





### TO BE REMOVED

def get_all_matches():
    all_matches = Match.query.all()
    return all_matches

def filter_past_matches(all_matches, filter_results=True, update_delay_h=2.5):
    """
    Returns a list of matches that are in the past.
    If filter_results is True, only matches with results (home_goals and away_goals) are returned.
    If filter_results is False, return all matches that started > 2.5h ago.
    """
    if not all_matches:
        all_matches = Match.query.all()

    past_matches = []
    if filter_results:
        past_matches = [m for m in all_matches 
                        if m.home_goals is not None and m.away_goals is not None]
    else:
        latest_start_time = datetime.now() - timedelta(minutes=60*update_delay_h)
        past_matches = [m for m in all_matches if m.play_date < latest_start_time]
    return sorted(
        past_matches, 
        key=lambda x: (x.round_number, x.play_date),
        reverse=True)
    

def all_past_matches_have_results(all_matches):
    """
    Returns True if all past matches have results (home_goals and away_goals).
    """
    return filter_past_matches(all_matches, filter_results=True) == \
        filter_past_matches(all_matches, filter_results=False)


def filter_next_matches(all_matches, n_max_days, n_min_hours=0.25):
    """
    Returns a list of matches that are in the future, and at least n_min_hours away.
    """
    if not all_matches:
        all_matches = Match.query.all()
    now = datetime.now()
    matches = [ m for m in all_matches 
               if (m.play_date >= now + timedelta(hours=n_min_hours)) and
               (m.play_date <= now + timedelta(days=n_max_days)) ]
    return sorted(matches, key=lambda x: x.play_date)

def print_matches(matches):
    """
    Prints a list of matches in a readable format.
    """
    for m in matches:
        print(f"{m.round_number} : {m.home_team} vs {m.away_team} ({m.play_date})")
        if m.home_goals is not None and m.away_goals is not None:
            print(f"  Result: {m.home_goals}:{m.away_goals}")
        else:
            print("  No result yet")
    print("")

def get_user_bets(user_id):
    user_bets = {}
    if user_id:
        for bet in Bet.query.filter_by(player_id=user_id).all():
            user_bets[bet.match_id] = bet
    return user_bets

def get_all_bets():
    """
    Returns a dict of all bets, grouped by match_id.
    """
    bets_by_match = {}
    all_bets = Bet.query.all()
    for bet in all_bets:
        if bet.match_id not in bets_by_match:
            bets_by_match[bet.match_id] = []
        
        bets_by_match[bet.match_id].append({
            'player_id': bet.player_id,
            'goals_home': bet.goals_home,
            'goals_away': bet.goals_away,
            'username': Player.query.get(bet.player_id).username,
            'username_short': Player.query.get(bet.player_id).username_short
        })
    return bets_by_match

def compute_scores(past_matches, all_bets):
    """
    Compute scores for each player based on their bets and the actual match results.
    Returns a list of dicts, 1 per player.
    """
    player_scores = {}

    for match in past_matches:
        match_bets = all_bets.get(match.id, [])
        for bet in match_bets:
            player_id = bet['player_id']
            if player_id not in player_scores:
                player_scores[player_id] = {
                    'username': bet['username'],
                    'username_short': bet['username_short'],
                    'n_exact': 0,
                    'n_correct': 0,
                    'n_bets_placed': 0,
                    'score': 0
                }
            ps = player_scores[player_id]
            ps['n_bets_placed'] += 1

            # check exact score
            if bet['goals_home'] == match.home_goals and bet['goals_away'] == match.away_goals:
                ps['n_exact'] += 1
                ps['score'] += 2
            # check correct outcome (H/U/B)
            elif ((bet['goals_home'] > bet['goals_away'] and match.home_goals > match.away_goals) or
                (bet['goals_home'] < bet['goals_away'] and match.home_goals < match.away_goals) or
                (bet['goals_home'] == bet['goals_away'] and match.home_goals == match.away_goals)):
                ps['n_correct'] += 1
                ps['score'] += 1

    # return as sorted list
    return sorted(player_scores.values(), key=lambda x: x['score'], reverse=True)


