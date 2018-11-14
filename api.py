from flask import Flask, jsonify
from scrape import get_browser, ESPN_BASE, SCOREBOARD_ENDPOINT, DATE_EXTENSION, get_soup, get_all_games

app = Flask(__name__)
browsers = {}
browsers['today'] = get_browser()
browsers['today'].get(ESPN_BASE + SCOREBOARD_ENDPOINT)

@app.route('/', methods=['GET'])
def home():
    return "<p>Scoreboard API</p>"

@app.route('/scoreboard')
def scoreboard():
	browsers['today'].refresh()
	soup = get_soup(browsers['today'].page_source)
	return jsonify(get_all_games(soup))

@app.route('/scoreboard/<date>')
def scoreboardByDate(date):
	if not date in browsers:
		print('loading again for ' + date)
		browsers[date] = get_browser()
		browsers[date].get(ESPN_BASE + SCOREBOARD_ENDPOINT + DATE_EXTENSION.format(date))
	soup = get_soup(browsers[date].page_source)
	return jsonify(get_all_games(soup))

@app.route('/boxscore/<game_id>')
def boxscore(game_id):
	with open('index.html', 'r') as file:
		soup = get_soup(file.read())

	return jsonify(get_boxscore(soup))

