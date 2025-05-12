import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta

db = SQLAlchemy() # ORM handle
migrate = Migrate() # ties into Alembic under the hood

DB_URI = os.getenv('FIFAGUTTA_DATABASE_URL')

### INITIALIZATION

def init_db(app):
    # Binds SQLAlchemy and Flask-Migrate to the Flask app.
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', DB_URI)
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    db.init_app(app)
    with app.app_context():
        db.create_all()   # ← creates all tables defined by your models
    migrate.init_app(app, db)




### CRUD functions
from .models import Player, Bet, Match 
from .scraper import ScheduleScraper



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


def filter_next_matches(all_matches, n_max_days=7, n_min_hours=0.25):
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
    Returns a  list of dicts, 1 per player.
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


## SCRAPER FCNS

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

