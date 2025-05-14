from .db import db

class Player(db.Model):
    __tablename__ = 'players'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50), unique=True, nullable=False)
    username_short = db.Column(db.String(10), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)



class Match(db.Model):
    __tablename__ = 'matches'
    id           = db.Column(db.Integer, primary_key=True)
    home_team    = db.Column(db.String(50), nullable=False)
    away_team    = db.Column(db.String(50), nullable=False)
    play_date    = db.Column(db.DateTime, nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    home_goals   = db.Column(db.Integer, nullable=True)
    away_goals   = db.Column(db.Integer, nullable=True)

    # never let me insert the same home+away+date twice.
    __table_args__ = (
      db.UniqueConstraint(
        'home_team', 'away_team', name='uix_home_away'),
    )


class Bet(db.Model):
    __tablename__ = 'bets'
    id         = db.Column(db.Integer, primary_key=True)
    player_id  = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    match_id   = db.Column(db.Integer, db.ForeignKey('matches.id'),  nullable=False)
    goals_home = db.Column(db.Integer, nullable=False)
    goals_away = db.Column(db.Integer, nullable=False)

    # Prevent the same player from betting twice on one match
    __table_args__ = (
      db.UniqueConstraint('player_id', 'match_id', name='uix_player_match'),
    )


