# setup.py
import os
from connection import get_db
from pymongo import ASCENDING
from crud_hotels import delete_hotels_without_geometry
from flatten import flatten_all_collections

def create_indexes():
    """Create necessary indexes for spatial queries"""
    db = get_db()
    
    collections_to_index = [
        ("hotels", "geometry"),
        ("cities", "geometry"),
        ("districts", "geometry"),
        ("tourist_attractions", "geometry"),
    ]
    
    print("Creating indexes...")
    for collection_name, field in collections_to_index:
        try:
            db[collection_name].create_index([(field, "2dsphere")])
            print(f"✓ Created 2dsphere index on {collection_name}.{field}")
        except Exception as e:
            print(f"✗ Failed to create index on {collection_name}: {e}")
    
    # Create text index for name searches
    try:
        db["hotels"].create_index([("properties.name", ASCENDING)])
        db["tourist_attractions"].create_index([("properties.name", ASCENDING)])
        print("✓ Created name indexes")
    except Exception as e:
        print(f"✗ Failed to create name indexes: {e}")

def setup():
    """Complete setup process"""
    print("=" * 60)
    print("SETTING UP GEOSPATIAL DATABASE")
    print("=" * 60)
    
    # Step 1: Flatten all collections
    print("\n1. Flattening collections...")
    flatten_all_collections()
    
    # Step 2: Create indexes
    print("\n2. Creating indexes...")
    create_indexes()
    
    # Step 3: Clean invalid data
    print("\n3. Cleaning data...")
    delete_hotels_without_geometry()
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("You can now run main.py to execute queries and visualizations.")
    
    # Show sample data
    from connection import hotels_col, tourist_attractions_col
    print(f"\nSample hotel: {hotels_col.find_one().get('properties', {}).get('name', 'Unnamed')}")
    print(f"\nSample attraction: {tourist_attractions_col.find_one().get('properties', {}).get('name', 'Unnamed')}")

if __name__ == "__main__":
    setup()