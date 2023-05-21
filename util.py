import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

default_batch_size = 30

def initialize_firebase():
    cred = credentials.Certificate("secrets/sportsdigest-gpt-firebase-adminsdk-mccm0-e20975b026.json")
    firebase_admin.initialize_app(cred)
    return firestore.client()