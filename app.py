from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session
from src.ball24 import TippeData24
from src.ball25 import TippeData25
from src.kampspill import Kampspill
import os
import json

app = Flask(__name__)

load_dotenv() # Load environment variables from .env file
app.secret_key = os.getenv('SECRET_KEY')
VALID_PASSWORDS = json.loads(os.getenv('PASSWORDS_JSON'))


@app.route('/')
def index():
    # This route serves the current year’s results (using, for example, obos25.html)
    balleball25 = TippeData25()
    balleball25.update_contestants()
    contestants = balleball25.get_sorted_contestants()
    contestants_json = [contestant.to_dict() for contestant in contestants]
    names = balleball25.get_sorted_names()
    standings = balleball25.standings
    return render_template(
        'obos25.html',
        standings=standings,
        names=names,
        contestants=contestants,
        contestants_json=contestants_json
    )

@app.route('/2024')
def last_year():
    # This route serves last year's minimal results using lastyear.html
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

@app.route('/matches')
def match_bets():
	kampspill = Kampspill(2025)
	next_matches = kampspill.get_next_matches(7)
	return render_template(
		'kampspill.html',
		next_matches=next_matches)


@app.route('/login', methods=['POST'])
def login():
    pw = request.json.get('password')
    username = VALID_PASSWORDS.get(pw)
    if username:
        session['username'] = username
        return jsonify({'success': True, 'username': username})
    else:
        return jsonify({'success': False}), 401




@app.route('/2023')
def hjelp():
	return "vi rykket ned"

if __name__ == "__main__":
	app.run(host="0.0.0.0", debug=True)
