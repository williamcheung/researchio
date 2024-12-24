from dotenv import load_dotenv
load_dotenv()

import os

from pymongo import MongoClient
from pymongo.collection import Collection

MONGODB_ATLAS_CLUSTER_URI=os.getenv('MONGODB_ATLAS_CLUSTER_URI')
DB_NAME=os.getenv('DB_NAME')
COLLECTION_NAME=os.getenv('COLLECTION_NAME')

def _get_user_stats_collection(client: MongoClient) -> Collection:
    db = client[DB_NAME] # creates if not exist
    return db.get_collection(COLLECTION_NAME)

# initialize user stats collection
with MongoClient(MONGODB_ATLAS_CLUSTER_URI) as client:
    _get_user_stats_collection(client).create_index('ip_address', unique=True) # idempotent

def persist_user_stats(ip_address: str, user_stats: dict[str, str]) -> bool:
    try:
        with MongoClient(MONGODB_ATLAS_CLUSTER_URI) as client:
            result = _get_user_stats_collection(client).update_one(
                        {'ip_address': ip_address},
                        {'$set': user_stats},
                        upsert = True)
            print(f'{COLLECTION_NAME} - {result}')
            return result.modified_count == 1 or result.upserted_id is not None
    except Exception as e:
        print(f'Error persisting user stats: {e}')
        return False

def get_user_stats(ip_address: str) -> dict[str, str]:
    try:
        with MongoClient(MONGODB_ATLAS_CLUSTER_URI) as client:
            user_stats = _get_user_stats_collection(client).find_one({'ip_address': ip_address})
            if user_stats: # may be `None`
                del user_stats['_id'] # caller doesn't care about this, uses `ip_address`
            return user_stats
    except Exception as e:
        print(f'Error retrieving user stats: {e}')
        return None
