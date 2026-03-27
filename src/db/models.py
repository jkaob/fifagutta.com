from . import db

class Player(db.Model):
    __tablename__  = 'players'
    id             = db.Column(db.Integer, primary_key=True)
    full_name      = db.Column(db.String(100), nullable=False)
    password       = db.Column(db.String(20), nullable=False)
    username       = db.Column(db.String(50), unique=True, nullable=True)
    username_short = db.Column(db.String(4), unique=True, nullable=True)
    email          = db.Column(db.String(40), unique=True, nullable=True)



# 2026-specific tables

class Team(db.Model):
    __tablename__ = 'teams26'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)



class Tabelltips26(db.Model):
    __tablename__ = 'tabelltips26'
    id        = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    team_name = db.Column(db.String(100), nullable=False)
    rank      = db.Column(db.Integer, nullable=False)

class Kampspill26(db.Model):
    __tablename__ = 'kampspill26'
    player_id    = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    num_points   = db.Column(db.Integer, nullable=False)
    num_bets     = db.Column(db.Integer, nullable=False)
    num_corrects = db.Column(db.Integer, nullable=False)
    num_hub      = db.Column(db.Integer, nullable=False) 

    
class Bet(db.Model):
    __tablename__ = 'bets26'
    id         = db.Column(db.Integer, primary_key=True)
    player_id  = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    match_id   = db.Column(db.Integer, db.ForeignKey('matches.id'),  nullable=False)
    goals_home = db.Column(db.Integer, nullable=False)
    goals_away = db.Column(db.Integer, nullable=False)

    # Prevent the same player from betting twice on one match
    __table_args__ = (
      db.UniqueConstraint('player_id', 'match_id', name='uix_player_match'),
    )

class Match(db.Model):
    __tablename__ = 'matches26'
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
