import os
from pymongo import MongoClient, ASCENDING

username = os.getenv("MONGO_USERNAME")
password = os.getenv("MONGO_PASSWORD")
host = os.getenv("MONGO_HOST", "localhost")
port = os.getenv("MONGO_PORT", "27017")

if not username or not password:
    MONGO_URI = "mongodb://localhost:27017/"
else:
    MONGO_URI = f"mongodb://{username}:{password}@{host}:{port}/"

MONGO_DBNAME = os.getenv("MONGO_DBNAME", "assignment")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "assignments")

client = MongoClient(MONGO_URI)
db = client[MONGO_DBNAME]
collection = db[MONGO_COLLECTION]

# Creazione indici
collection.create_index([("teacherSerialNumber", ASCENDING)])
collection.create_index([("students", ASCENDING)])
