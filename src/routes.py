import os
import json
from flask import Blueprint, request, session, jsonify, render_template
from .kampspill import Kampspill
from datetime import datetime
from .models import Match, Bet, Player
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .db      import db


# Login route
VALID_PASSWORDS = json.loads(os.getenv('FIFAGUTTA_PASSWORDS_JSON'))
UNAME_SHORT = json.loads(os.getenv('FIFAGUTTA_UNAME_SHORT_JSON'))
auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/login', methods=['POST'])
def login():
    print("attempting login")
    data = request.get_json() or {}
    pw   = data.get('password', '')
    username = VALID_PASSWORDS.get(pw)
    if not username:
        return jsonify({'success': False}), 401
    
    username_short = UNAME_SHORT.get(username)

    # lookup or create the Player record
    player = Player.query.filter_by(username=username).first()
    if not player:
        player = Player(username=username,
                        password_hash='',   # or store the pw-hash if you like
                        username_short=username_short)
        db.session.add(player)
        db.session.commit()
        print("Add player ID ", player.id)

    # update the username_short if it has changed / is not set
    if player.username_short != username_short:
        player.username_short = username_short
        db.session.commit()
        print("Update player ID ", player.id)

    # store in session
    session['user_id']   = player.id
    session['username']  = player.username
    session['username_short']  = player.username_short

    return jsonify({
        'success': True, 
        'username': player.username, 
        'user_id': player.id, 
        'username_short': player.username_short}), 200
    

# Bets route
bets_bp = Blueprint('bets', __name__)
@bets_bp.route('/place_bet', methods=['POST'])
def place_bet():
    # 1) check login
    player_id = session.get('user_id')
    if not player_id:
        return jsonify({ 'success': False, 'error': 'not_logged_in' }), 401
    
    # 2) parse JSON body
    data = request.get_json() or {}
    match_id   = data.get('match_id')
    goals_home = data.get('home')
    goals_away = data.get('away')

    # 3) validate inputs
    if match_id is None or goals_home is None or goals_away is None:
        return jsonify({ 'success': False, 'error': 'missing_fields' }), 400
    try:
        match_id   = int(match_id)
        goals_home = int(goals_home)
        goals_away = int(goals_away)
    except ValueError:
        return jsonify({ 'success': False, 'error': 'invalid_values' }), 400

    # upsert: either create new Bet or overwrite existing
    try:
        bet = Bet.query.filter_by(player_id=player_id, match_id=match_id).first()
        if not bet:
            bet = Bet(
              player_id=player_id, match_id=match_id, goals_home=goals_home, goals_away=goals_away)
            db.session.add(bet)
        else:
            print(f"bet already existing (ID {bet.id}:  {bet.goals_home} - {bet.goals_away})")
            pass
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({ 'success': False, 'error': 'db_error', 'details': str(e) }), 500


    return jsonify({
      'success':    True,
      'bet': {
        'id':         bet.id,
        'player_id':  bet.player_id,
        'match_id':   bet.match_id,
        'goals_home': bet.goals_home,
        'goals_away': bet.goals_away
      }
    }), 200


# Match storage Routes
matches_bp = Blueprint('matches', __name__)
@matches_bp.route('/matches')
def show_match_bets():
    user_id = session.get('user_id') # try to get user_id from session
    print("user_id", user_id)

    # get nect matches via scraper, add to database if not existing
    kampspill = Kampspill(2025)
    raw_next = kampspill.get_next_matches()
    next_matches = ensure_matches_in_db(raw_next)

    raw_past = kampspill.get_past_matches()
    past_matches = ensure_past_matches_in_db(raw_past)

    # 2) load this user’s bets into a dict { match_id: Bet }
    user_bets = {}
    if user_id:
        for bet in Bet.query.filter_by(player_id=user_id).all():
            user_bets[bet.match_id] = bet

    # 3) load all bets on a match into a list of bet-dicts
    all_bets = get_all_bets()

    # 4) compute scores for each player
    player_scores = compute_scores(past_matches, all_bets)

    return render_template(
        'kampspill.html',
        next_matches=next_matches,
        past_matches=past_matches,
        user_bets=user_bets,
        bets_by_match=all_bets,
        player_scores=player_scores,
    )


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

########################################
######      Helper functions      ######
########################################

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
                print("Updating match ID", match_obj.id)
            match_obj.home_goals = m['home_goals']
            match_obj.away_goals = m['away_goals']

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            print("Conflict on match:", m['home_team'], m['away_team'])

        db_matches.append(match_obj)

    return db_matches


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