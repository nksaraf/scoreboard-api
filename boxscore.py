from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

ESPN_BASE = 'http://www.espn.com'
SCOREBOARD_ENDPOINT = '/nba/scoreboard'
BOXSCORE_ENDPOINT = '/nba/boxscore?gameId={}'
GAME_ID = '401070880'
DATE_EXTENSION = '/_/date/{}'
LOGO_URL = 'http://a.espncdn.com/i/teamlogos/nba/500/{}.png'

BOXSCORE_HEADER = [
	'MIN',
	'FG',
	'3PT',
	'FT',
	'OREB',
	'DREB',
	'REB',
	'AST',
	'STL',
	'BLK',
	'TO',
	"PF",
	'+/-',
	'PTS'
]

BOXSCORE_ORDER = [0, 13, 7, 6, 1, 2, 3, 8, 9, 10, 11, 12, 4, 5]

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

def dump(data, filename):
	import json
	with open(filename, 'w') as file:
		file.write(json.dumps(data, indent=4))


# boxscore: {
# 	home: {
# 		starters: [
# 			{
# 				name: 
# 				id: 
# 				position
# 				stats: []
# 			}
# 		],
# 		bench: {

# 		},
# 		totals: []
# 	},
# 	away: {

# 	}
# }

def parse_player(player_soup):
	cols = player_soup.find_all('td')
	name = cols[0]
	stats_soup = cols[1:]
	if len(stats_soup) == 1:
		stats = get_text(stats_soup[0])
	else:
		stats = []
		for stat in stats_soup:
			stats.append(get_text(stat))

	player = {
		'name': get_text(name.find('span')),
		'url': name.find('a')['href'],
		'position': get_text(name.find('span', class_='position')),
		'stats': [stats[i] for i in BOXSCORE_ORDER]
	}

	return player

def parse_team_total(total_soup):
	cols = total_soup.find_all('td')
	name = cols[0]
	stats_soup = cols[1:]
	stats = []
	for stat in stats_soup:
		stats.append(get_text(stat))

	return stats

def parse_team_boxscore(box_soup):
	table = box_soup.find('table', class_='mod-data')

	starters_soup = table.find('tbody')
	starters = [parse_player(player_soup) for player_soup in starters_soup.find_all('tr')]

	bench_soup = table.find('tbody', class_='bench')
	bench = [parse_player(player_soup) for player_soup in bench_soup.find_all('tr')[:-2]]

	return {
		'starters': starters,
		'bench': bench,
		'total': parse_team_total(bench_soup.find('tr', class_='totals'))
	}


def get_boxscore(soup):
	container = soup.find('div', id='gamepackage-boxscore-module')
	if container is None:
		return {}

	home = parse_team_boxscore(container.find('div', class_='gamepackage-home-wrap'))
	away = parse_team_boxscore(container.find('div', class_='gamepackage-away-wrap'))

	return {
		'home': home,
		'away': away,
		'header': [BOXSCORE_HEADER[i] for i in BOXSCORE_ORDER]
	}


if __name__ == '__main__':
	# browser = get_browser()
	# browser.get(ESPN_BASE + BOXSCORE_ENDPOINT.format(GAME_ID))
	with open('index.html', 'r') as file:
		soup = get_soup(file.read())

	boxscore = get_boxscore(soup)
	dump(boxscore, 'boxscore.json')