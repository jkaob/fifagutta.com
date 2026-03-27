import json
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask import Blueprint, request, session, jsonify, render_template
from flask import redirect, url_for
from ..db.functions import *
from ..db.functions import (
    get_upcoming_matches,
    get_user_bets_for_matches,
    get_player_scores
)


from ..app_globals import DEFAULT_N_DAYS

bets_bp = Blueprint('kamspill', __name__)



@bets_bp.route('/home')
def display_matches_html():
    user_id = session.get('user_id') # try to get user_id from session
    print("user_id", user_id)

    # 1) Fetch next matches
    n_future_days = request.args.get('n_future_days', default=DEFAULT_N_DAYS, type=int)
    now = datetime.now(datetime.timezone.utc)
    end = now + timedelta(days=n_future_days)
    print(f"range: {now} to {end} ({n_future_days} days)")

    # DB query should return only next matches in range
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
        n_future_days=n_future_days
    )


@bets_bp.route('/display_past')
def display_past_matches():
    past_matches = get_finished_matches()
    
    from collections import defaultdict
    def group_matches_by_round(matches):
        grouped = defaultdict(list)
        for match in matches:
            grouped[match.round_number].append(match)
        return dict(grouped)

    past_matches_grouped = group_matches_by_round(past_matches)
    return past_matches_grouped


# TODO: Make it all faster
# Match storage Routes
@bets_bp.route('/display_deprecated')
def display_matches_html_deprecated():
    user_id = session.get('user_id') # try to get user_id from session
    print("user_id", user_id)

    # 1) get matches from database
    all_matches = get_all_matches()

    n_future_days = request.args.get('n_future_days', default=DEFAULT_N_DAYS, type=int)

    print("n_future_days", n_future_days)

    past_matches = filter_past_matches(all_matches)
    next_matches = filter_next_matches(all_matches, n_max_days=n_future_days)

    # print_matches(past_matches)
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
        n_future_days=n_future_days
    )






# Bets route
@bets_bp.route('/place_kamspill', methods=['POST'])
def place_bet():
    print("running place_bet")
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

    # upsert: either create new Bet or overwrite existing
    try:
        bet = add_bet_to_db(db, user_id, match_id, goals_home, goals_away)
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

@bets_bp.route('/place_all_kamspill', methods=['POST'])
def place_all_kamspill():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    bets_data = request.form.get('bets_json')
    n_future_days = request.form.get('n_future_days', default=DEFAULT_N_DAYS, type=int)
    
    if not bets_data:
        return redirect(url_for('matches.display_matches_html', n_future_days=n_future_days))

    bets = json.loads(bets_data)

    for match_id_str, bet in bets.items():
        match_id = int(match_id_str)
        goals_home = bet.get("home")
        goals_away = bet.get("away")

        if goals_home is not None and goals_away is not None:
            add_bet_to_db(db, user_id, match_id, goals_home, goals_away)

    return redirect(url_for('matches.display_matches_html', n_future_days=n_future_days))



@bets_bp.route('/update_db', methods=['POST'])
def update_database():
    """
    Gets the latest matches from the scraper and updates the database if needed
    NB: This should already have been done by workflow
    """

    n_future_days = request.args.get('n_future_days', default=DEFAULT_N_DAYS, type=int)
    print("update-db/n_future_days", n_future_days)
    add_matches_to_db(n_future_days, 0.25, False)
    return redirect(url_for('matches.display_matches_html', n_future_days=n_future_days))  # replace with your actual route name

