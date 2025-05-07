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
auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    pw   = data.get('password', '')
    username = VALID_PASSWORDS.get(pw)
    if not username:
        return jsonify({'success': False}), 401
    
    # lookup or create the Player record
    player = Player.query.filter_by(username=username).first()
    if not player:
        player = Player(username=username,
                        password_hash='')  # or store the pw-hash if you like
        db.session.add(player)
        db.session.commit()
        print("Add player ID ", player.id)

    # store in session
    session['user_id']   = player.id
    session['username']  = player.username

    return jsonify({'success': True, 'username': player.username, 'user_id': player.id})
    

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
    raw = kampspill.get_next_matches(7)
    next_matches = ensure_matches_in_db(raw)


    # 2) load this user’s bets into a dict { match_id: Bet }
    user_bets = {}
    if user_id:
        for bet in Bet.query.filter_by(player_id=user_id).all():
            user_bets[bet.match_id] = bet

    return render_template(
        'kampspill.html',
        next_matches=next_matches,
        user_bets=user_bets
    )





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
                away_team=m['away_team'],
                play_date=play_date
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
                    away_team=m['away_team'],
                    play_date=play_date
                ).first()
        db_matches.append(match_obj)
    return db_matches