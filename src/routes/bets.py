import json
import traceback
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, session, jsonify, render_template
from flask import redirect, url_for
from ..db import db
from ..db.models import Bet, Player
from ..db.db_functions import (
    get_upcoming_matches,
    get_user_bets_for_matches,
    get_player_scores,
    get_finished_matches,
    add_bet_to_db,
    add_matches_to_db
)


from ..app_globals import DEFAULT_N_DAYS

bets_bp = Blueprint('bets', __name__)

@bets_bp.route('/home')
def display_matches_html():
    user_id = session.get('user_id') # try to get user_id from session
    print("user_id", user_id)

    # 1) Fetch next matches
    n_future_days = request.args.get('n_future_days', default=DEFAULT_N_DAYS, type=int)
    now = datetime.now(timezone(timedelta(hours=1)))
    end = now + timedelta(days=n_future_days)
    print(f"range: {now} to {end} ({n_future_days} days)")
    
    next_matches = get_upcoming_matches(start=now, end=end, n_max=50)

    # 2) load bets for upcoming matches for this user
    user_bets = get_user_bets_for_matches(user_id=user_id, match_ids = [m.id for m in next_matches])

    # 3) get scores to make a standings table
    player_scores = get_player_scores()

    return render_template(
        'kampspill26.html',
        next_matches=next_matches,
        user_bets=user_bets,
        player_scores=player_scores,
        n_future_days=n_future_days,
        past_matches={},  # Empty on initial load
        bets_by_match={}   # Empty on initial load
    )


@bets_bp.route('/display_past')
def display_past_matches():
    """
    Fetch past matches, group by round, and get all bets for those matches.
    Returns JSON for AJAX loading.
    """
    from collections import defaultdict
    
    past_matches = get_finished_matches()
    
    # Group by round
    grouped = defaultdict(list)
    for match in past_matches:
        grouped[match.round_number].append(match)
    past_matches_grouped = dict(grouped)

    # Get all bets for these matches
    match_ids = [m.id for m in past_matches]
    all_bets_raw = Bet.query.filter(Bet.match_id.in_(match_ids)).all()
    
    player = Player.query.get(bet.player_id)

    # Format bets for template
    bets_by_match = {}
    for bet in all_bets_raw:
        if bet.match_id not in bets_by_match:
            bets_by_match[bet.match_id] = []
        bets_by_match[bet.match_id].append({
            'id': bet.id,
            'goals_home': bet.goals_home,
            'goals_away': bet.goals_away,
            'username': player.username,
            'username_short': player.username_short
        })
    
    return render_template(
        'kampspill-past.html',
        past_matches=past_matches_grouped,
        bets_by_match=bets_by_match
    )



# Bets route
@bets_bp.route('/place_bet', methods=['POST'])
def place_bet():
    print("running /place_bet")
    # 1) check login
    user_id = session.get('user_id')
    if not user_id:
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
    
    
    try:
        bet = add_bet_to_db(user_id, match_id, goals_home, goals_away, commit=True)
        if not bet:
            raise RuntimeError("add_bet_to_db returned None")
    except SQLAlchemyError as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'db_error', 'details': str(e)}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'unhandled', 'details': str(e)}), 500



    return jsonify({
        'success': True,
        'bet_id': bet.id,
        'match_id': bet.match_id,
        'home': bet.goals_home,
        'away': bet.goals_away
    }), 200

@bets_bp.route('/place_all_bets', methods=['POST'])
def place_all_bets():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    bets_data = request.form.get('bets_json')
    n_future_days = request.form.get('n_future_days', default=DEFAULT_N_DAYS, type=int)
    if not bets_data:
        return redirect(url_for('bets.display_matches_html', n_future_days=n_future_days))

    bets = json.loads(bets_data)

    try:
        # one transaction
        for match_id_str, bet_data in bets.items():
            match_id = int(match_id_str)
            goals_home = int(bet_data.get("home"))
            goals_away = int(bet_data.get("away"))
            add_bet_to_db(user_id, match_id, goals_home, goals_away, commit=False)

        db.session.commit()
    except (ValueError, SQLAlchemyError) as err:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'db_error', 'details': str(e)}), 500

    return redirect(url_for('bets.display_matches_html', n_future_days=n_future_days))



@bets_bp.route('/update_db', methods=['POST'])
def update_database():
    """
    Gets the latest matches from the scraper and updates the database if needed
    NB: This should already have been done by workflow
    """

    n_future_days = request.args.get('n_future_days', default=DEFAULT_N_DAYS, type=int)
    print("update-db/n_future_days", n_future_days)
    add_matches_to_db(n_future_days, 0.25, False)
    return redirect(url_for('bets.display_matches_html', n_future_days=n_future_days))  # replace with your actual route name

