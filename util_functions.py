import firebase_admin
import secret_keys
import json
import traceback
import logging
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud import secretmanager

default_batch_size = 30

def initialize_firebase(app_context):
    if app_context == "local":
        cred = credentials.Certificate("secrets/sportsdigest-gpt-firebase-adminsdk-mccm0-e20975b026.json")
        firebase_admin.initialize_app(cred)
        return firestore.client()
    elif app_context == "gcp":
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{secret_keys.gcp_project_id}/secrets/{secret_keys.gcp_secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        db_secret_string = response.payload.data.decode("UTF-8")
        db_secret_json = json.loads(db_secret_string)
        firebase_admin.initialize_app(credentials.Certificate(db_secret_json))
        return firestore.client()

def clear_collection(db, collection_name):
    coll_ref = db.collection(collection_name)
    docs = coll_ref.limit(default_batch_size).stream()
    deleted = 0

    for doc in docs:
        logging.info(f"Deleting doc {doc.id} => {doc.to_dict()}")
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
    
def error_handler(exception):
    logging.error(f"An error occurred: {type(exception).__name__}")
    logging.error(f"Error message: {str(exception)}")
    logging.error("Here is the traceback:")
    traceback.print_exc()