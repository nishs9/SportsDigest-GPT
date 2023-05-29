import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

default_batch_size = 30

def initialize_firebase(app_name=None):
    cred = credentials.Certificate("secrets/sportsdigest-gpt-firebase-adminsdk-mccm0-e20975b026.json")
    if app_name == None:
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app(cred, name=app_name)
    return firestore.client()

def clear_collection(db, collection_name):
    coll_ref = db.collection(collection_name)
    docs = coll_ref.limit(default_batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f"Deleting doc {doc.id} => {doc.to_dict()}")
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= default_batch_size:
        return clear_collection(db, collection_name)

def get_team_name_by_id(db, team_id):
    team_doc_ref = db.collection('teams').document(team_id).get()
    if team_doc_ref.exists:
        return team_doc_ref.to_dict()['full_name']
    else:
        return None

def get_team_abbrev_by_id(db, team_id):
    team_doc_ref = db.collection('teams').document(team_id).get()
    if team_doc_ref.exists:
        return team_doc_ref.to_dict()['abbreviation']
    else:
        return None