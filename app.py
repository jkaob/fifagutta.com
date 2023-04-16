from flask import Flask, render_template
from ball import Scraper, TippeData

app = Flask(__name__)

ball = TippeData()

@app.route('/')
def index():
	ball.update()
	dict = ball.data_dict
	standings = ball.standings
	sorted_names = ball.get_sorted_names()
	return render_template('index.html', standings=standings, data_dict=dict, names_sorted=sorted_names)


@app.route('/test')
def test():
	return 'Test works!'

if __name__ == "__main__":
	app.run(debug=True)
