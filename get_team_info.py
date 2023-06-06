import requests
import util_functions as util

# Saves team info to the teams collection in the database
def save_team_info(db):
    team_info_url = "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams"
    
    response = requests.get(team_info_url)
    data = response.json()

    for team in data['sports'][0]['leagues'][0]['teams']:
        team_data = {
            'abbreviation': team['team']['abbreviation'],
            'full_name': team['team']['displayName'],
            'location': team['team']['location'],
            'mascot': team['team']['name'],
        }

        doc_ref = db.collection('teams').document(team['team']['id'])
        doc_ref.set(team_data)

# Wrapper function for the save_team_info function
def update_team_collection():
    db = util.initialize_firebase()
    util.clear_collection(db, 'teams')
    save_team_info(db)

if __name__ == "__main__":
    update_team_collection()
