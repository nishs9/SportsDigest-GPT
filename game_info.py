import requests
import util
import pandas as pd
from bs4 import BeautifulSoup

def save_upcoming_game_info(db):
    url = "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    response = requests.get(url)
    data = response.json()

    for game in data['events']:
        game_short_name = game['shortName'].split(' @ ')
        unique_game_id = game['id'] + "-" + game_short_name[0] + "-" + game_short_name[1]

        game_data = {
            'home_team': game['competitions'][0]['competitors'][0]['team']['displayName'],
            'home_team_id': game['competitions'][0]['competitors'][0]['team']['id'],
            'away_team': game['competitions'][0]['competitors'][1]['team']['displayName'],
            'away_team_id': game['competitions'][0]['competitors'][1]['team']['id'],
            'short_detail': game['status']['type']['shortDetail'],
            'is_summarized': False,
        }

        doc_ref = db.collection('games').document(unique_game_id)
        doc_ref.set(game_data)

def get_unsummarized_games(db):
    game_ids = []
    games_to_summarize = db.collection('games').where('is_summarized', '==', False).stream()

    for game in games_to_summarize:
        curr_dict = {
            "game_id": game.id, 
            "home_team_id": game.to_dict()["home_team_id"], 
            "away_team_id": game.to_dict()["away_team_id"]
        }
        game_ids.append(curr_dict)

    return game_ids

def get_single_game_boxscore_data(db, game_dict):
    game_id = game_dict['game_id'].split('-')[0]

    away_team_full_name = util.get_team_name_by_id(db, game_dict['away_team_id'])
    home_team_full_name = util.get_team_name_by_id(db, game_dict['home_team_id'])

    away_team_abbrev = util.get_team_abbrev_by_id(db, game_dict['away_team_id'])
    home_team_abbrev = util.get_team_abbrev_by_id(db, game_dict['home_team_id'])

    boxscore_header = away_team_full_name + " vs " + home_team_full_name + " Box Score\n\n"

    url = f'https://www.espn.com/mlb/boxscore/_/gameId/{game_id}'

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    tables = soup.find_all('table')

    boxscore_tables = ""
    for i, table in enumerate(tables):
        if i == 0:
            continue
        elif i == 10:
            break

        columns = [th.text for th in table.find('tr').find_all('th')]

        data_rows = table.find_all('tr')[1:]
        data = [[td.text for td in row.find_all('td')] for row in data_rows]

        df = pd.DataFrame(data, columns=columns)

        with open("test_files/test.txt", 'a') as f:
            f.write(df.to_string())
            f.write('\n\n')

        boxscore_tables += df.to_string(index=False) + "\n\n"

    boxscore_data = {
            'home_team': home_team_full_name,
            'home_team_id': game_dict['home_team_id'],
            'away_team': away_team_full_name,
            'away_team_id': game_dict['away_team_id'],
            'game_ref_id': game_id,
            'boxscore_content': boxscore_header + boxscore_tables,
            'is_summarized': False,
    }

    unique_boxscore_id = game_id + "-" + away_team_abbrev + "-" + home_team_abbrev + "-boxscore"

    doc_ref = db.collection('boxscores').document(unique_boxscore_id)
    doc_ref.set(boxscore_data)

def update_game_collection():
    db = util.initialize_firebase()
    util.clear_collection(db, 'games')
    save_upcoming_game_info(db)
    game_ids = get_unsummarized_games(db)
    for game in game_ids:
        get_single_game_boxscore_data(db, game)

if __name__ == "__main__":
    #update_game_collection()
    #game_ids = get_unsummarized_games(util.initialize_firebase())
    test = [{"game_id": "401471766", "home_team_id": "10", "away_team_id": "1"}]
    get_single_game_boxscore_data(util.initialize_firebase(), test[0])
