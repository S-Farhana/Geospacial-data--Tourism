# flatten.py (UPDATED)
from connection import (
    hotels_col,
    cities_col,
    districts_col,
    tourist_attractions_col,
    state_boundary_col
)

def flatten_collection(collection, new_collection_name=None):
    """
    Flatten a GeoJSON FeatureCollection into individual documents.
    If new_collection_name is provided, creates a new collection.
    Otherwise, replaces the existing one.
    """
    doc = collection.find_one()
    
    if not doc:
        print(f"Collection {collection.name} is empty")
        return 0
    
    if "features" not in doc:
        print(f"Collection {collection.name} is already flattened or not a FeatureCollection")
        return collection.count_documents({})
    
    features = doc["features"]
    
    if new_collection_name:
        # Create new collection
        new_collection = collection.database[new_collection_name]
        new_collection.delete_many({})
        new_collection.insert_many(features)
        print(f"Inserted {len(features)} features into new collection '{new_collection_name}'")
        return len(features)
    else:
        # Replace existing collection
        collection.delete_many({})
        collection.insert_many(features)
        print(f"Flattened {collection.name}: {len(features)} documents")
        return len(features)

def flatten_all_collections():
    """Flatten all collections that are FeatureCollections"""
    
    print("Flattening all collections...")
    
    # Flatten hotels (already done)
    hotel_count = flatten_collection(hotels_col)
    
    # Flatten cities
    city_count = flatten_collection(cities_col)
    
    # Flatten districts
    district_count = flatten_collection(districts_col)
    
    # Flatten tourist attractions
    attraction_count = flatten_collection(tourist_attractions_col)
    
    # Note: state_boundary might be a single feature, not a FeatureCollection
    state = state_boundary_col.find_one()
    if state and "features" in state:
        state_count = flatten_collection(state_boundary_col)
    else:
        print(f"State boundary is already a single document: {state_boundary_col.count_documents({})}")
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Hotels: {hotel_count}")
    print(f"Cities: {city_count}")
    print(f"Districts: {district_count}")
    print(f"Tourist Attractions: {attraction_count}")
    
    return True

if __name__ == "__main__":
    flatten_all_collections()