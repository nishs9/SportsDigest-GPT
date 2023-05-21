import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

default_batch_size = 30

def initialize_firebase():
    cred = credentials.Certificate("secrets/sportsdigest-gpt-firebase-adminsdk-mccm0-e20975b026.json")
    firebase_admin.initialize_app(cred)
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