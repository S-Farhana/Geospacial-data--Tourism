from pymongo import MongoClient
from urllib.parse import quote_plus

USERNAME = quote_plus("23pd10_db_user")
PASSWORD = quote_plus("Farhana@786")

MONGO_URI = f"mongodb+srv://{USERNAME}:{PASSWORD}@tn-geospatial.dwpaxur.mongodb.net/?retryWrites=true&w=majority"

DB_NAME = "tn_gis"


def get_db():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db


def sanity_checks(db):
    print("Databases:", db.client.list_database_names())
    print("Collections:", db.list_collection_names())

    for col in db.list_collection_names():
        count = db[col].count_documents({})
        print(f"{col}: {count} documents")


db = get_db()
sanity_checks(db)

cities_col = db["cities"]
districts_col = db["districts"]
district_boundary_col = db["district_boundary"]
hotels_col = db["hotels"]
state_boundary_col = db["state_boundary"]
tourist_attractions_col = db["tourist_attractions"]
