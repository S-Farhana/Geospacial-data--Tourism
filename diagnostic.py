# diagnostic.py
from connection import (
    hotels_col,
    cities_col,
    districts_col,
    tourist_attractions_col,
    state_boundary_col
)

def check_collection(collection, name):
    """Check a collection and print stats"""
    count = collection.count_documents({})
    print(f"\n{name.upper()}:")
    print(f"  Total documents: {count}")
    
    if count > 0:
        sample = collection.find_one()
        print(f"  Sample document keys: {list(sample.keys())}")
        if "properties" in sample:
            print(f"  Sample properties: {list(sample['properties'].keys())[:10]}...")
        if "geometry" in sample:
            print(f"  Sample geometry type: {sample['geometry']['type']}")
    
    return count

def check_indexes(collection, name):
    """Check if collection has indexes"""
    indexes = list(collection.index_information().keys())
    print(f"  Indexes: {indexes}")
    
    # Check for 2dsphere index
    has_2dsphere = any('2dsphere' in str(index) for index in indexes)
    if not has_2dsphere and collection.count_documents({}) > 0:
        print(f"  WARNING: {name} has no 2dsphere index!")

def main():
    print("=" * 60)
    print("DATABASE DIAGNOSTICS")
    print("=" * 60)
    
    collections = [
        (hotels_col, "Hotels"),
        (cities_col, "Cities"),
        (districts_col, "Districts"),
        (tourist_attractions_col, "Tourist Attractions"),
        (state_boundary_col, "State Boundary")
    ]
    
    total = 0
    for collection, name in collections:
        count = check_collection(collection, name)
        check_indexes(collection, name)
        total += count
    
    print("\n" + "=" * 60)
    print(f"TOTAL DOCUMENTS ACROSS ALL COLLECTIONS: {total}")
    
    # Check for Marina Beach
    print("\n" + "=" * 60)
    print("SEARCHING FOR ATTRACTIONS")
    print("=" * 60)
    
    # Try different name variations
    search_terms = ["Marina", "Beach", "Rajaji", "Memorial", "Temple", "Fort"]
    
    for term in search_terms:
        results = list(tourist_attractions_col.find(
            {"properties.name": {"$regex": term, "$options": "i"}},
            {"properties.name": 1, "_id": 0}
        ).limit(5))
        
        if results:
            names = [r.get("properties", {}).get("name") for r in results]
            print(f"\nFound attractions with '{term}':")
            for name in names:
                if name:
                    print(f"  - {name}")

if __name__ == "__main__":
    main()