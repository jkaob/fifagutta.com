from flask import Flask, render_template
from ball24 import TippeData24
from ball25 import TippeData25
#from ball23 import TippeDataBase

app = Flask(__name__)

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

@app.route('/24')
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



#
# #ball = TippeDataBase()
# @app.route('/')
# def index():
# 	balleball25 = TippeData25()
# 	balleball25.update_contestants()
# 	contestants = balleball25.get_sorted_contestants()
# 	contestants_json = [contestant.to_dict() for contestant in contestants]
# 	names = balleball25.get_sorted_names()
# 	standings = balleball25.standings
# 	return render_template(
# 		'index.html',
# 		standings=standings,
# 		names=names,
# 		contestants=contestants,
# 		contestants_json=contestants_json
# 	)
#
# @app.route('/2024')
# def index24():
# 	balleball24 = TippeData24()
# 	balleball24.update_contestants(fetch=Falses)
# 	contestants = balleball24.get_sorted_contestants()
# 	contestants_json = [contestant.to_dict() for contestant in contestants]
# 	names = balleball24.get_sorted_names()
# 	standings = balleball24.standings
# 	return render_template(
# 		'r-24.html',
# 		standings=standings,
# 		names=names,
# 		contestants=contestants,
# 		contestants_json=contestants_json
# 	)
#

@app.route('/2023')
def hjelp():
	return "vi rykket ned"

@app.route('/test')
def test():
	return 'Test works!'

if __name__ == "__main__":
	app.run(debug=True)
