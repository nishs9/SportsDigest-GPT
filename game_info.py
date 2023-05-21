import requests
import util

def save_upcoming_game_info(db):
    url = "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    response = requests.get(url)
    data = response.json()

    for game in data['events']:
        game_short_name = game['shortName'].split(' @ ')
        unique_game_id = game['id'] + "-" + game_short_name[0] + game_short_name[1]

        game_data = {
            'game_id': unique_game_id,
            'home_team': game['competitions'][0]['competitors'][0]['team']['displayName'],
            'home_team_id': game['competitions'][0]['competitors'][0]['team']['id'],
            'away_team': game['competitions'][0]['competitors'][1]['team']['displayName'],
            'away_team_id': game['competitions'][0]['competitors'][1]['team']['id'],
            'short_detail': game['status']['type']['shortDetail'],
            'is_summarized': False,
        }

        db.collection('games').add(game_data)

def update_game_collection():
    db = util.initialize_firebase()
    util.clear_collection(db, 'games')
    save_upcoming_game_info(db)

if __name__ == "__main__":
    update_game_collection()