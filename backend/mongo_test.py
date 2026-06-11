from pymongo import MongoClient
import certifi
from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

print("1) ENV PATH:", ENV_PATH)
print("2) ENV FILE EXISTS:", ENV_PATH.exists())

load_dotenv(dotenv_path=ENV_PATH)

MONGO_URI = os.getenv("MONGO_URI")

print("3) MONGO_URI exists:", bool(MONGO_URI))
print("4) MONGO_URI preview:", MONGO_URI[:40] + "..." if MONGO_URI else None)

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000
)

try:
    result = client.admin.command("ping")
    print("5) PING OK:", result)
except Exception as e:
    print("5) PING ERROR:", str(e))