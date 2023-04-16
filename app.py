from flask import Flask, render_template
from ball import Scraper, TippeData

app = Flask(__name__)

ball = TippeData()

@app.route('/')
def index():
	ball.update()
	dict_sorted = ball.get_sorted_dict()
	names = ball.get_sorted_names()
	standings = ball.standings
	return render_template('index.html', standings=standings, names=names, data_dict=dict_sorted)


@app.route('/test')
def test():
	return 'Test works!'

if __name__ == "__main__":
	app.run(debug=True)
