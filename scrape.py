from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

ESPN_BASE = 'http://www.espn.com'
SCOREBOARD_ENDPOINT = '/nba/scoreboard'
DATE_EXTENSION = '/_/date/{}'
LOGO_URL = 'http://a.espncdn.com/i/teamlogos/nba/500/{}.png'

GAME_STATES = {
	'pregame': 0,
	'live': 1,
	'final': 2
}

def get_browser():
	options = Options()
	options.headless = True
	return webdriver.Chrome(options=options)

def get_soup(html):
	return BeautifulSoup(html, 'lxml')

def get_text(tag):
	return tag.get_text().strip()

def parse_team(team_soup):
	abbrevName = get_text(team_soup.find('span', class_='sb-team-abbrev'))
	meta = team_soup.find('div', class_='sb-meta')

	team = {
		'shortName': get_text(team_soup.find('span', class_='sb-team-short')),
		'abbreviation': abbrevName,
		'teamUrl': ESPN_BASE + meta.find('a')['href'],
		'logoUrl': LOGO_URL.format(abbrevName.lower()),
		'record': get_text(meta.find('p', class_='overall'))
	}

	total_soup = team_soup.find('td', class_='total')
	if total_soup is not None and get_text(total_soup) != '':
		total = int(get_text(total_soup))
	else:
		total = 0

	periods = []
	periods_soup = team_soup.find_all('td', class_='score')
	if len(periods_soup) > 0:
		for period_soup in periods_soup:
			if get_text(period_soup) != '':
				periods.append(int(get_text(period_soup)))
			else:
				periods.append(0)
	else:
		periods = [0, 0, 0, 0]

	return team, total, periods

def parse_highlight(game_soup):
	detail_soup = game_soup.find('section', class_='sb-detail')
	if detail_soup is None:
		return { 'type': 'none', 'description': '' }
	else:
		return { 
			'type': 'highlight', 
			'description': get_text(detail_soup.find('p'))
		}

def parse_last_play(game_soup):
	detail_soup = game_soup.find('section', class_='sb-detail')
	if detail_soup is None:
		return { 'type': 'none', 'description': '' }
	else:
		return { 
			'type': 'last_play', 
			'description': get_text(detail_soup.find('p'))
		}

def parse_pregame(game_soup):
	detail_soup = game_soup.find('section', class_='sb-detail')
	if detail_soup is None:
		return { 'type': 'none', 'description': '' }
	else:
		return { 
			'type': 'pregame', 
			'description': get_text(detail_soup.find('div', class_='stat').findChild())
		}

def parse_status(game_soup):
	state = -1
	statusDescription = 'none'

	for key in GAME_STATES.keys():
		if key in game_soup["class"]:
			state = GAME_STATES[key]
			statusDescription = key

	game_soup.find('tr', class_='sb-linescore')
	if state in [0, 2]:
		clock = 0

	parse_info_func = [parse_pregame, parse_last_play, parse_highlight]

	situation = get_text(game_soup.find('th', class_='date-time'))

	status = {
		'state': state,
		'situation': situation,
		'info': parse_info_func[state](game_soup),
	}

	return status

def parse_game(game_soup):
	homeTeam, homeTotal, homePeriods = parse_team(game_soup.find('tr', class_='home'))
	awayTeam, awayTotal, awayPeriods = parse_team(game_soup.find('tr', class_='away'))
	homeTeam['id'] = int(game_soup['data-homeid'])
	awayTeam['id'] = int(game_soup['data-awayid'])

	status = parse_status(game_soup)
	winner = ''
	if status['state'] == 2:
		winner = 'home' if homeTotal > awayTotal else 'away'
	status['winner'] = winner

	game = {
		'id': game_soup['id'],
		'url': ESPN_BASE + game_soup.find('a', class_='mobileScoreboardLink')['href'],
		'teams': {
			'home': homeTeam,
			'away': awayTeam
		},
		'score': {
			'totals': {
				'home': homeTotal,
				'away': awayTotal
			},
			'periods': {
				'home': homePeriods,
				'away': awayPeriods
			}
		},
		'description': awayTeam['abbreviation'] + ' @ ' + homeTeam['abbreviation'],
		'status': status
	}

	return game

def dump(data, filename):
	import json
	with open(filename, 'w') as file:
		file.write(json.dumps(data, indent=4))


def get_all_games(soup):
	games_soup = soup.find_all('article', class_='scoreboard')
	games = {'games': [parse_game(game_soup) for game_soup in games_soup]}
	return games


if __name__ == '__main__':
	browser = get_browser()
	browser.get(ESPN_BASE + SCOREBOARD_ENDPOINT)
	soup = get_soup(browser.page_source)
