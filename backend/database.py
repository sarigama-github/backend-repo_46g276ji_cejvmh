import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "reseller_db")

_client: Optional[MongoClient] = None
_db = None

def get_db():
    global _client, _db
    if _db is not None:
        return _db
    _client = MongoClient(DATABASE_URL)
    _db = _client[DATABASE_NAME]
    return _db


def collection(name: str) -> Collection:
    return get_db()[name]


def create_document(collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    col = collection(collection_name)
    now = datetime.utcnow()
    data_with_meta = {**data, "created_at": now, "updated_at": now}
    inserted = col.insert_one(data_with_meta)
    return col.find_one({"_id": inserted.inserted_id})


def get_documents(collection_name: str, filter_dict: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
    col = collection(collection_name)
    cursor = col.find(filter_dict or {}).sort("created_at", -1).limit(limit)
    return list(cursor)


def update_document(collection_name: str, _id, update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    col = collection(collection_name)
    update_set = {**update, "updated_at": datetime.utcnow()}
    col.update_one({"_id": _id}, {"$set": update_set})
    return col.find_one({"_id": _id})
