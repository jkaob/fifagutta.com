from flask import Flask, render_template
from ball24 import TippeData24
#from ball23 import TippeData

app = Flask(__name__)

#ball = TippeData()
balleball = TippeData24()

@app.route('/')
def index():
	balleball.update_contestants()
	contestants = balleball.get_sorted_contestants()
	contestants_json = [contestant.to_dict() for contestant in contestants]
	names = balleball.get_sorted_names()
	standings = balleball.standings
	return render_template(
		'obos.html',
		standings=standings,
		names=names,
		contestants=contestants, 
		contestants_json=contestants_json
	)
	

@app.route('/2023')
def hjelp():
	return "vi rykket ned"
	# ball.update()
	# dict_sorted = ball.get_sorted_dict()
	# names = ball.get_sorted_names()
	# standings = ball.standings
	# history_length = ball.min_played
	# return render_template('index.html',
	# 						standings=standings,
	# 						names=names,
	# 						data_dict=dict_sorted,
	# 						history_length=history_length
	# 						)


@app.route('/test')
def test():
	return 'Test works!'

if __name__ == "__main__":
	app.run(debug=True)
