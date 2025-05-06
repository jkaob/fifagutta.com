
from flask import Blueprint, request, session, jsonify, render_template
from .kampspill import Kampspill
from datetime import datetime
from .models import Match, Bet, Player
from sqlalchemy.exc import IntegrityError
from .db      import db

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


### ROUTES
bets_bp = Blueprint('bets', __name__)

@bets_bp.route('/place_bet', methods=['POST'])
def place_bet():
    # assume user is logged in and "user_id" is in session
    player_id = session.get('user_id')
    if not player_id:
        return jsonify({'error': 'not logged in'}), 401

    match_id   = request.form['match_id']
    goals_home = int(request.form['home'])
    goals_away = int(request.form['away'])

    # upsert: either create new Bet or overwrite existing
    bet = Bet.query.filter_by(player_id=player_id, match_id=match_id).first()
    if not bet:
        bet = Bet(player_id=player_id, match_id=match_id)
        db.session.add(bet)
    bet.goals_home = goals_home
    bet.goals_away = goals_away
    db.session.commit()

    return jsonify({'success': True})


matches_bp = Blueprint('matches', __name__)
@matches_bp.route('/matches')
def show_match_bets():
    kampspill = Kampspill(2025)
    raw = kampspill.get_next_matches(7)
    matches = ensure_matches_in_db(raw)
    return render_template('kampspill.html', next_matches=matches)