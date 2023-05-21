import requests
import util

def clear_teams_collection(db):
    coll_ref = db.collection('teams')
    docs = coll_ref.limit(util.default_batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f"Deleting doc {doc.id} => {doc.to_dict()}")
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= util.default_batch_size:
        return clear_teams_collection(db)

def save_team_info(db):
    team_info_url = "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams"
    
    response = requests.get(team_info_url)
    data = response.json()

    for team in data['sports'][0]['leagues'][0]['teams']:
        data = {
            'abbreviation': team['team']['abbreviation'],
            'espn_id': team['team']['id'],
            'full_name': team['team']['displayName'],
            'location': team['team']['location'],
            'mascot': team['team']['name'],
        }

        db.collection('teams').add(data)

def update_team_collection():
    db = util.initialize_firebase()
    clear_teams_collection(db)
    save_team_info(db)

if __name__ == "__main__":
    update_team_collection()
