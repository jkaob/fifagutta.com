import os

# load environemnt variables from .env file
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ.setdefault(key,value.strip().strip('"').strip("'"))

import pymysql
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from src.ball24 import TippeData24
from src.ball25 import TippeData25
from src.ball26 import TippeData26
from src.db import init_db
from src.routes import bets_bp, matches_bp, auth_bp, register_bp
import json
pymysql.install_as_MySQLdb()

app = Flask(__name__)



# Load environment variables
app.secret_key = os.getenv('FIFAGUTTA_SECRET_KEY')

# set up database and register blueprints
init_db(app)
app.register_blueprint(auth_bp)
app.register_blueprint(register_bp)
app.register_blueprint(bets_bp)
app.register_blueprint(matches_bp)

@app.route('/')
def index():
    balleball26 = TippeData26()
    balleball26.update_standings_only(fetch=True)
    return render_template(
        'preseason.html',
        standings=balleball26.standings
    )

'''
@app.route('/')
def index():
    balleball26 = TippeData26()
    balleball26.update_contestants()
    contestants = balleball26.get_sorted_contestants()
    contestants_json = [contestant.to_dict() for contestant in contestants]
    names = balleball26.get_sorted_names()
    standings = balleball26.standings
    return render_template(
        'obos26.html',
        standings=standings,
        names=names,
        contestants=contestants,
        contestants_json=contestants_json
    )
'''

@app.route('/2025')
def r25():
    # This route serves last year's minimal results using lastyear.html
    balleball25 = TippeData25()
    balleball25.update_contestants(fetch=False)
    contestants = balleball25.get_sorted_contestants()
    contestants_json = [contestant.to_dict() for contestant in contestants]
    names = balleball25.get_sorted_names()
    standings = balleball25.standings
    return render_template(
        'r-25.html',
        standings=standings,
        names=names,
        contestants=contestants,
        contestants_json=contestants_json
    )

@app.route('/2024')
def r24():
    balleball24 = TippeData24()
    balleball24.update_contestants(fetch=False)
    contestants = balleball24.get_sorted_contestants()
    contestants_json = [contestant.to_dict() for contestant in contestants]
    names = balleball24.get_sorted_names()
    standings = balleball24.standings
    return render_template(
        'r-24.html',
        standings=standings,
        names=names,
        contestants=contestants,
        contestants_json=contestants_json
    )


@app.route('/2023')
def hjelp():
	return "vi rykket ned"

if __name__ == "__main__":
	app.run(host="0.0.0.0", debug=True)
