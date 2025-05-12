import os
import json
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask import Blueprint, request, session, jsonify, render_template
from .db      import *
from .models import Player, Bet, Match


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

    # 1) get matches from database
    all_matches = get_all_matches()

    past_matches = filter_past_matches(all_matches)
    next_matches = filter_next_matches(all_matches)

    print_matches(past_matches)
    from collections import defaultdict
    def group_matches_by_round(matches):
        grouped = defaultdict(list)
        for match in matches:
            grouped[match.round_number].append(match)
        return dict(grouped)
    past_matches_grouped = group_matches_by_round(past_matches)


    # 2) load this user’s bets into a dict { match_id: Bet }
    user_bets = get_user_bets(user_id)

    # 3) load all bets on each match into a list of bet-dicts
    all_bets = get_all_bets()

    # 4) compute scores for each player
    player_scores = compute_scores(past_matches, all_bets)

    return render_template(
        'kampspill.html',
        next_matches=next_matches,
        past_matches=past_matches_grouped,
        user_bets=user_bets,
        bets_by_match=all_bets,
        player_scores=player_scores,
    )


@matches_bp.route('/update-db', methods=['POST'])
def update_database():
    """
    Gets the latest matches from the scraper and updates the database if needed
    """
    add_matches_to_db(7, 0.25, False)



