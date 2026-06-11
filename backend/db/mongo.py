from pymongo import MongoClient
from core.config import MONGO_URI, DB_NAME
import certifi

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000
)

db = client[DB_NAME]

users_collection = db["users"]
documents_collection = db["documents"]
analyses_collection = db["analyses"]
chats_collection = db["chats"]