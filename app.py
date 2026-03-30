import os

# load environemnt variables from .env file (local build)
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ.setdefault(key,value.strip().strip('"').strip("'"))

import pymysql
from flask import Flask, render_template
from src.ball.ball24 import TippeData24
from src.ball.ball25 import TippeData25
from src.ball.ball26 import TippeData26
from src.reader import CsvKampspill
from src.db import init_db
from src.routes import register_blueprints
from src.app_globals import is_before_deadline, is_before_seriestart, is_preseason, SERIESTART, DEADLINE
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# Load environment variables
app.secret_key = os.getenv('FIFAGUTTA_SECRET_KEY')

# set up database and register blueprints
init_db(app)
register_blueprints(app)

app.jinja_env.globals["g_BEFORE_DEADLINE"] = is_before_deadline()
app.jinja_env.globals["g_PRESEASON"] = is_preseason()


# PRESEASON
if is_preseason():
    @app.route('/')
    def index():
        balleball26 = TippeData26()
        balleball26.update_standings_only(fetch=True)
        return render_template(
            'preseason.html',
            standings=balleball26.standings,
            is_before_deadline=is_before_deadline(),
            seriestart=SERIESTART.isoformat(),
            deadline=DEADLINE.isoformat()
        )
else:
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
            contestants_json=contestants_json,
            is_before_seriestart=is_before_seriestart(),
            seriestart=SERIESTART.isoformat()
        )


@app.route('/2025')
def r25():
    # This route serves last year's minimal results using lastyear.html
    balleball25 = TippeData25()
    balleball25.update_contestants(fetch=False)
    contestants = balleball25.get_sorted_contestants()
    contestants_json = [contestant.to_dict() for contestant in contestants]
    names = balleball25.get_sorted_names()
    standings = balleball25.standings
    kampspill_scores = CsvKampspill(f"data/2025-kampspill.csv").get_results()
    return render_template(
        'r-25.html',
        standings=standings,
        names=names,
        contestants=contestants,
        contestants_json=contestants_json,
        kampspill_scores=kampspill_scores
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
