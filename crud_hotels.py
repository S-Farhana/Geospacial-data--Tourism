# from datetime import datetime
# from pprint import pprint

# from connection import hotels_col, tourist_attractions_col

# def insert_hotel(feature: dict):
#     """
#     Insert a full GeoJSON Feature into hotels collection.
#     """
#     if not feature:
#         raise ValueError("Feature is empty")

#     if "geometry" not in feature or "type" not in feature["geometry"]:
#         raise ValueError("Invalid or missing GeoJSON geometry")

#     if "properties" not in feature:
#         feature["properties"] = {}

#     feature["properties"]["created_at"] = datetime.utcnow()

#     result = hotels_col.insert_one(feature)
#     print(f"Hotel inserted with ID: {result.inserted_id}")


# def get_hotels_in_city(city_name: str):
#     """
#     Fetch hotels located in a given city.
#     """
#     query = {
#         "properties.addr:city": {
#             "$regex": f"^{city_name}$",
#             "$options": "i"
#         }
#     }

#     projection = {
#         "properties.name": 1,
#         "properties.stars": 1,
#         "properties.addr:city": 1,
#         "geometry": 1,
#         "_id": 0
#     }

#     results = list(hotels_col.find(query, projection))
#     print(f"Hotels found in {city_name}: {len(results)}")
#     return results


# def update_hotel_rating(hotel_name: str, new_stars: int):
#     """
#     Update star rating of a hotel.
#     """
#     result = hotels_col.update_one(
#         {"properties.name": hotel_name},
#         {
#             "$set": {
#                 "properties.stars": new_stars,
#                 "properties.updated_at": datetime.utcnow()
#             }
#         }
#     )

#     if result.matched_count == 0:
#         print("No hotel found with that name")
#     else:
#         print(f"Updated rating for '{hotel_name}' to {new_stars}")


# def delete_tourist_attraction(attraction_name: str):
#     """
#     Delete a tourist attraction by name.
#     """
#     result = tourist_attractions_col.delete_one(
#         {"properties.name": attraction_name}
#     )

#     if result.deleted_count == 0:
#         print("No attraction found to delete")
#     else:
#         print(f"Deleted attraction: {attraction_name}")

# def get_one_hotel():
#     """
#     Fetch and print one hotel document.
#     """
#     hotel = hotels_col.find_one()
#     pprint(hotel)

# def get_hotel_by_name(hotel_name: str):
#     """
#     Fetch a hotel by exact name.
#     """
#     hotel = hotels_col.find_one(
#         {"properties.name": hotel_name}
#     )

#     if hotel:
#         pprint(hotel)
#         return hotel
#     else:
#         print("Hotel not found")
#         return None

# def get_hotels_without_city():
#     """
#     Find hotels where addr:city is missing or null.
#     """
#     query = {
#         "$or": [
#             {"properties.addr:city": {"$exists": False}},
#             {"properties.addr:city": None}
#         ]
#     }

#     results = list(hotels_col.find(query, {
#         "properties.name": 1,
#         "geometry": 1,
#         "_id": 0
#     }))

#     print(f"Hotels without city info: {len(results)}")
#     return results
# def get_hotels_by_star_rating(min_stars: int):
#     """
#     Fetch hotels with stars >= min_stars.
#     """
#     query = {
#         "properties.stars": {"$gte": min_stars}
#     }

#     results = list(hotels_col.find(query, {
#         "properties.name": 1,
#         "properties.stars": 1,
#         "geometry": 1,
#         "_id": 0
#     }))

#     print(f"Hotels with ≥ {min_stars} stars: {len(results)}")
#     return results

# def delete_hotel_by_name(hotel_name: str):
#     """
#     Delete a single hotel by name.
#     """
#     result = hotels_col.delete_one(
#         {"properties.name": hotel_name}
#     )

#     if result.deleted_count == 0:
#         print(" No hotel deleted")
#     else:
#         print(f"Deleted hotel: {hotel_name}")

# def delete_hotels_without_geometry():
#     """
#     Remove invalid hotel documents without geometry.
#     """
#     result = hotels_col.delete_many(
#         {"geometry": {"$exists": False}}
#     )

#     print(f"🧹 Removed {result.deleted_count} invalid hotel records")

# def count_hotels():
#     count = hotels_col.count_documents({})
#     print(f"Total hotels: {count}")
#     return count

# def check_field_existence(field_path: str):
#     """
#     Count documents that contain a specific field.
#     """
#     count = hotels_col.count_documents(
#         {field_path: {"$exists": True}}
#     )

#     print(f"Documents with '{field_path}': {count}")
#     return count


# crud_hotels.py (COMPLETE IMPROVED VERSION)
from datetime import datetime
from pprint import pprint
from connection import hotels_col, tourist_attractions_col


def insert_hotel(feature: dict):
    """
    Insert a full GeoJSON Feature into hotels collection with validation.
    """
    if not feature:
        raise ValueError("Feature is empty")

    if "geometry" not in feature:
        raise ValueError("Missing geometry field")
    
    if "type" not in feature["geometry"] or feature["geometry"]["type"] != "Point":
        raise ValueError("Invalid geometry type - must be 'Point'")
    
    if "coordinates" not in feature["geometry"] or not feature["geometry"]["coordinates"]:
        raise ValueError("Missing or empty coordinates")
    
    # Validate coordinates
    coords = feature["geometry"]["coordinates"]
    if len(coords) < 2:
        raise ValueError(f"Invalid coordinates format: {coords}")
    
    lon, lat = coords[0], coords[1]
    if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
        raise ValueError(f"Coordinates must be numeric: lon={lon}, lat={lat}")
    
    if abs(lon) > 180 or abs(lat) > 90:
        raise ValueError(f"Invalid coordinate values: lon={lon}, lat={lat}")

    if "properties" not in feature:
        feature["properties"] = {}
    
    # Ensure required fields
    if "name" not in feature["properties"] or not feature["properties"]["name"]:
        feature["properties"]["name"] = "Unnamed Hotel"
    
    if "tourism" not in feature["properties"]:
        feature["properties"]["tourism"] = "hotel"
    
    # Add timestamps
    feature["properties"]["created_at"] = datetime.utcnow()
    feature["properties"]["updated_at"] = datetime.utcnow()
    
    # Set type if not present
    if "type" not in feature:
        feature["type"] = "Feature"

    result = hotels_col.insert_one(feature)
    print(f"✓ Hotel inserted with ID: {result.inserted_id}")
    print(f"  Name: {feature['properties'].get('name')}")
    print(f"  Location: {lon:.4f}, {lat:.4f}")
    return result.inserted_id


def get_hotels_in_city(city_name: str, limit=50):
    """
    Fetch hotels located in a given city with improved query.
    """
    if not city_name or not isinstance(city_name, str):
        print(f"Invalid city name: {city_name}")
        return []
    
    query = {
        "properties.addr:city": {
            "$regex": f"^{city_name}$",
            "$options": "i"
        }
    }

    projection = {
        "properties.name": 1,
        "properties.stars": 1,
        "properties.addr:city": 1,
        "properties.website": 1,
        "properties.tourism": 1,
        "properties.addr:street": 1,
        "geometry": 1,
        "_id": 0
    }

    try:
        results = list(hotels_col.find(query, projection).limit(limit))
        print(f"✓ Found {len(results)} hotels in '{city_name}'")
        
        if results:
            print(f"  First 5 hotels in {city_name}:")
            for i, hotel in enumerate(results[:5], 1):
                name = hotel.get('properties', {}).get('name', 'Unnamed')
                stars = hotel.get('properties', {}).get('stars', 'N/A')
                print(f"    {i}. {name} ({stars} stars)")
        else:
            print(f"  No hotels found in '{city_name}'")
            
        return results
    except Exception as e:
        print(f"✗ Error fetching hotels in {city_name}: {e}")
        return []


def update_hotel_rating(hotel_name: str, new_stars: int):
    """
    Update star rating of a hotel with validation.
    """
    if not hotel_name or not isinstance(hotel_name, str):
        print("Invalid hotel name")
        return
    
    if not isinstance(new_stars, int) or new_stars < 0 or new_stars > 5:
        print(f"Invalid star rating: {new_stars}. Must be between 0-5")
        return
    
    # First check if hotel exists
    existing = hotels_col.find_one({"properties.name": hotel_name})
    if not existing:
        print(f"✗ No hotel found with name: '{hotel_name}'")
        print("  Available hotel names (first 10):")
        hotels = list(hotels_col.find({}, {"properties.name": 1}).limit(10))
        for i, hotel in enumerate(hotels, 1):
            name = hotel.get('properties', {}).get('name')
            if name:
                print(f"    {i}. {name}")
        return
    
    old_stars = existing.get('properties', {}).get('stars', 'N/A')
    
    result = hotels_col.update_one(
        {"properties.name": hotel_name},
        {
            "$set": {
                "properties.stars": new_stars,
                "properties.updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        print(f"✗ No hotel found with name: '{hotel_name}'")
    else:
        print(f"✓ Updated rating for '{hotel_name}' from {old_stars} to {new_stars} stars")
        print(f"  {result.modified_count} document modified")


def delete_tourist_attraction(attraction_name: str):
    """
    Delete a tourist attraction by name.
    """
    if not attraction_name:
        print("No attraction name provided")
        return
    
    # First check if attraction exists
    existing = tourist_attractions_col.find_one({"properties.name": attraction_name})
    if not existing:
        print(f"✗ No attraction found with name: '{attraction_name}'")
        return
    
    result = tourist_attractions_col.delete_one(
        {"properties.name": attraction_name}
    )

    if result.deleted_count == 0:
        print(f"✗ No attraction deleted for '{attraction_name}'")
    else:
        print(f"✓ Deleted attraction: '{attraction_name}'")
        print(f"  {result.deleted_count} document removed")


def get_one_hotel(include_id=False):
    """
    Fetch and print one hotel document with complete info.
    """
    projection = {
        "properties.name": 1,
        "properties.stars": 1,
        "properties.addr:city": 1,
        "properties.website": 1,
        "properties.tourism": 1,
        "properties.addr:street": 1,
        "properties.addr:country": 1,
        "properties.phone": 1,
        "geometry": 1
    }
    
    if include_id:
        projection["_id"] = 1
    
    hotel = hotels_col.find_one({}, projection)
    
    if hotel:
        print("✓ Sample Hotel Document:")
        print("-" * 40)
        
        # Display basic info
        props = hotel.get('properties', {})
        name = props.get('name', 'Unnamed')
        city = props.get('addr:city', 'Unknown')
        stars = props.get('stars', 'N/A')
        
        print(f"Name: {name}")
        print(f"City: {city}")
        print(f"Stars: {stars}")
        
        # Display geometry
        if 'geometry' in hotel and 'coordinates' in hotel['geometry']:
            coords = hotel['geometry']['coordinates']
            if len(coords) >= 2:
                print(f"Location: {coords[0]:.4f}, {coords[1]:.4f}")
        
        # Display other properties
        other_props = {k: v for k, v in props.items() 
                      if k not in ['name', 'addr:city', 'stars'] and v}
        if other_props:
            print("\nOther Properties:")
            for key, value in other_props.items():
                print(f"  {key}: {value}")
        
        print("-" * 40)
        return hotel
    else:
        print("✗ No hotels found in database")
        return None


def get_hotel_by_name(hotel_name: str, exact_match=True):
    """
    Fetch a hotel by name with flexible matching.
    """
    if not hotel_name or not isinstance(hotel_name, str):
        print("Invalid hotel name")
        return None
    
    projection = {
        "properties.name": 1,
        "properties.stars": 1,
        "properties.addr:city": 1,
        "properties.website": 1,
        "properties.tourism": 1,
        "properties.addr:street": 1,
        "geometry": 1,
        "_id": 0
    }
    
    if exact_match:
        query = {"properties.name": hotel_name}
    else:
        query = {"properties.name": {"$regex": hotel_name, "$options": "i"}}
    
    hotel = hotels_col.find_one(query, projection)

    if hotel:
        print(f"✓ Found hotel: '{hotel_name}'")
        
        props = hotel.get('properties', {})
        name = props.get('name', 'Unnamed')
        city = props.get('addr:city', 'Unknown')
        stars = props.get('stars', 'N/A')
        
        print(f"  Name: {name}")
        print(f"  City: {city}")
        print(f"  Stars: {stars}")
        
        if 'geometry' in hotel and 'coordinates' in hotel['geometry']:
            coords = hotel['geometry']['coordinates']
            if len(coords) >= 2:
                print(f"  Location: {coords[0]:.4f}, {coords[1]:.4f}")
        
        return hotel
    else:
        print(f"✗ Hotel '{hotel_name}' not found")
        
        # Suggest similar names
        if exact_match:
            print("  Searching for similar names...")
            similar_hotels = list(hotels_col.find(
                {"properties.name": {"$regex": hotel_name, "$options": "i"}},
                {"properties.name": 1}
            ).limit(5))
            
            if similar_hotels:
                print("  Did you mean:")
                for i, h in enumerate(similar_hotels, 1):
                    name = h.get('properties', {}).get('name')
                    if name:
                        print(f"    {i}. {name}")
        
        return None


def get_hotels_without_city():
    """
    Find hotels where addr:city is missing or null.
    """
    query = {
        "$or": [
            {"properties.addr:city": {"$exists": False}},
            {"properties.addr:city": None}
        ]
    }

    results = list(hotels_col.find(query, {
        "properties.name": 1,
        "geometry": 1,
        "_id": 0
    }))

    print(f"Hotels without city info: {len(results)}")
    return results


def get_hotels_by_star_rating(min_stars: int, max_stars: int = 5, limit=100):
    """
    Fetch hotels with stars between min_stars and max_stars (inclusive).
    """
    if not isinstance(min_stars, int) or min_stars < 0:
        print(f"Invalid minimum stars: {min_stars}")
        return []
    
    if not isinstance(max_stars, int) or max_stars > 5 or max_stars < min_stars:
        print(f"Invalid maximum stars: {max_stars}")
        return []
    
    query = {
        "properties.stars": {"$gte": min_stars, "$lte": max_stars}
    }

    projection = {
        "properties.name": 1,
        "properties.stars": 1,
        "properties.addr:city": 1,
        "properties.website": 1,
        "geometry": 1,
        "_id": 0
    }

    results = list(hotels_col.find(query, projection).limit(limit))
    
    if min_stars == max_stars:
        print(f"✓ Found {len(results)} hotels with exactly {min_stars} stars")
    else:
        print(f"✓ Found {len(results)} hotels with {min_stars}-{max_stars} stars")
    
    if results:
        rating_text = f"{min_stars}-{max_stars}" if min_stars != max_stars else str(min_stars)
        print(f"  First 10 hotels with {rating_text} stars:")
        for i, hotel in enumerate(results[:10], 1):
            name = hotel.get('properties', {}).get('name', 'Unnamed')
            stars = hotel.get('properties', {}).get('stars', 'N/A')
            city = hotel.get('properties', {}).get('addr:city', 'Unknown')
            print(f"    {i}. {name} in {city} ({stars} stars)")
    else:
        print(f"  No hotels found with {min_stars}+ stars")
    
    return results


def delete_hotel_by_name(hotel_name: str):
    """
    Delete a single hotel by name.
    """
    if not hotel_name:
        print("No hotel name provided")
        return
    
    # First check if hotel exists
    existing = hotels_col.find_one({"properties.name": hotel_name})
    if not existing:
        print(f"✗ No hotel found with name: '{hotel_name}'")
        return
    
    result = hotels_col.delete_one(
        {"properties.name": hotel_name}
    )

    if result.deleted_count == 0:
        print(f"✗ No hotel deleted for '{hotel_name}'")
    else:
        print(f"✓ Deleted hotel: '{hotel_name}'")
        print(f"  {result.deleted_count} document removed")


def delete_hotels_without_geometry():
    """
    Remove invalid hotel documents without geometry or with invalid geometry.
    """
    # Find hotels without geometry
    no_geometry_query = {
        "$or": [
            {"geometry": {"$exists": False}},
            {"geometry": None},
            {"geometry": {}},
            {"geometry.type": {"$ne": "Point"}}
        ]
    }
    
    no_geometry_count = hotels_col.count_documents(no_geometry_query)
    
    # Find hotels with invalid coordinates
    invalid_coords_query = {
        "geometry.type": "Point",
        "$or": [
            {"geometry.coordinates": {"$exists": False}},
            {"geometry.coordinates": None},
            {"geometry.coordinates": []},
            {"geometry.coordinates.0": {"$type": "array"}},  # Nested array
            {"geometry.coordinates.1": {"$exists": False}}
        ]
    }
    
    invalid_coords_count = hotels_col.count_documents(invalid_coords_query)
    
    total_invalid = no_geometry_count + invalid_coords_count
    
    if total_invalid == 0:
        print("✓ No invalid hotel records found")
        return 0
    
    print(f"Found {total_invalid} invalid hotel records:")
    print(f"  - {no_geometry_count} without valid geometry")
    print(f"  - {invalid_coords_count} with invalid coordinates")
    
    # Delete hotels without geometry
    result1 = hotels_col.delete_many(no_geometry_query)
    
    # Delete hotels with invalid coordinates
    result2 = hotels_col.delete_many(invalid_coords_query)
    
    total_deleted = result1.deleted_count + result2.deleted_count
    print(f"✓ Removed {total_deleted} invalid hotel records")
    
    return total_deleted


def count_hotels():
    """
    Count total hotels in collection.
    """
    count = hotels_col.count_documents({})
    print(f"✓ Total hotels in database: {count}")
    return count


def check_field_existence(field_path: str):
    """
    Count documents that contain a specific field (non-null).
    """
    if not field_path:
        print("No field path provided")
        return 0
    
    query = {
        field_path: {"$exists": True, "$ne": None}
    }
    
    count = hotels_col.count_documents(query)
    print(f"✓ Documents with non-null '{field_path}': {count}")
    
    # Also show some sample values
    if count > 0:
        sample_hotels = list(hotels_col.find(
            {field_path: {"$exists": True, "$ne": None}},
            {field_path: 1, "properties.name": 1}
        ).limit(3))
        
        print(f"  Sample values for '{field_path}':")
        for i, hotel in enumerate(sample_hotels, 1):
            name = hotel.get('properties', {}).get('name', 'Unnamed')
            
            # Extract value from nested field path
            value = hotel
            for part in field_path.split('.'):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
            
            print(f"    {i}. {name}: {value}")
    
    return count


def get_sample_hotels(limit=10, with_city=None):
    """
    Get sample hotels for testing/display.
    """
    query = {}
    if with_city:
        query = {"properties.addr:city": with_city}
    
    projection = {
        "properties.name": 1,
        "properties.stars": 1,
        "properties.addr:city": 1,
        "properties.tourism": 1,
        "properties.website": 1,
        "geometry": 1,
        "_id": 0
    }
    
    hotels = list(hotels_col.find(query, projection).limit(limit))
    
    if with_city:
        print(f"✓ Retrieved {len(hotels)} sample hotels from {with_city}:")
    else:
        print(f"✓ Retrieved {len(hotels)} sample hotels:")
    
    for i, hotel in enumerate(hotels, 1):
        name = hotel.get('properties', {}).get('name', 'Unnamed')
        city = hotel.get('properties', {}).get('addr:city', 'Unknown')
        stars = hotel.get('properties', {}).get('stars', 'N/A')
        
        location = ""
        if 'geometry' in hotel and 'coordinates' in hotel['geometry']:
            coords = hotel['geometry']['coordinates']
            if len(coords) >= 2:
                location = f" @ {coords[0]:.4f}, {coords[1]:.4f}"
        
        print(f"    {i}. {name} ({stars} stars) in {city}{location}")
    
    return hotels


def search_hotels(keyword: str, field: str = "name", limit=20):
    """
    Search hotels by keyword in specified field.
    """
    if not keyword or not field:
        print("Keyword and field are required")
        return []
    
    query_field = f"properties.{field}"
    query = {
        query_field: {"$regex": keyword, "$options": "i"}
    }
    
    projection = {
        "properties.name": 1,
        "properties.stars": 1,
        "properties.addr:city": 1,
        "geometry": 1,
        "_id": 0
    }
    
    results = list(hotels_col.find(query, projection).limit(limit))
    print(f"✓ Found {len(results)} hotels matching '{keyword}' in {field}")
    
    if results:
        print(f"  First {min(5, len(results))} results:")
        for i, hotel in enumerate(results[:5], 1):
            name = hotel.get('properties', {}).get('name', 'Unnamed')
            city = hotel.get('properties', {}).get('addr:city', 'Unknown')
            stars = hotel.get('properties', {}).get('stars', 'N/A')
            print(f"    {i}. {name} in {city} ({stars} stars)")
    
    return results


def get_hotel_statistics():
    """
    Get statistics about hotels.
    """
    stats = {}
    
    # Total count
    stats['total_hotels'] = hotels_col.count_documents({})
    
    # Count by city
    pipeline = [
        {"$match": {"properties.addr:city": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$properties.addr:city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    top_cities = list(hotels_col.aggregate(pipeline))
    stats['top_cities'] = top_cities
    
    # Count by star rating
    star_pipeline = [
        {"$match": {"properties.stars": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$properties.stars", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    
    star_distribution = list(hotels_col.aggregate(star_pipeline))
    stats['star_distribution'] = star_distribution
    
    # Hotels without city
    stats['hotels_without_city'] = hotels_col.count_documents({
        "$or": [
            {"properties.addr:city": {"$exists": False}},
            {"properties.addr:city": None},
            {"properties.addr:city": ""}
        ]
    })
    
    # Print statistics
    print("=" * 50)
    print("HOTEL STATISTICS")
    print("=" * 50)
    print(f"Total Hotels: {stats['total_hotels']}")
    print(f"Hotels without city info: {stats['hotels_without_city']}")
    
    print("\nTop 10 Cities by Hotel Count:")
    for city in stats['top_cities']:
        print(f"  {city['_id']}: {city['count']} hotels")
    
    print("\nStar Rating Distribution:")
    for rating in stats['star_distribution']:
        stars = rating['_id']
        count = rating['count']
        bar = "★" * int(stars) if isinstance(stars, (int, float)) else ""
        print(f"  {stars} stars: {count} hotels {bar}")
    
    print("=" * 50)
    
    return stats


def create_sample_hotel(city="Chennai"):
    """
    Create a sample hotel for testing.
    """
    sample_hotel = {
        "type": "Feature",
        "properties": {
            "name": f"Test Hotel {datetime.now().strftime('%H%M%S')}",
            "tourism": "hotel",
            "stars": 3,
            "addr:city": city,
            "website": f"https://testhotel.example",
            "phone": "+91 44 12345678",
            "addr:street": "Test Street",
            "description": "A test hotel created for demonstration"
        },
        "geometry": {
            "type": "Point",
            "coordinates": [80.2707 + (datetime.now().microsecond % 100) * 0.0001, 
                          13.0827 + (datetime.now().microsecond % 100) * 0.0001]
        }
    }
    
    return sample_hotel


def main_test():
    """
    Test function to verify all CRUD operations.
    """
    print("=" * 60)
    print("CRUD HOTELS - TEST SUITE")
    print("=" * 60)
    
    # 1. Get statistics
    print("\n1. HOTEL STATISTICS")
    get_hotel_statistics()
    
    # 2. Get one hotel
    print("\n2. SAMPLE HOTEL")
    get_one_hotel()
    
    # 3. Get hotels in Chennai
    print("\n3. HOTELS IN CHENNAI")
    chennai_hotels = get_hotels_in_city("Chennai", limit=5)
    
    # 4. Search for a hotel
    print("\n4. SEARCH HOTELS")
    search_hotels("hotel", "tourism", limit=5)
    
    # 5. Get hotels without city
    print("\n5. HOTELS WITHOUT CITY INFO")
    get_hotels_without_city(limit=5)
    
    # 6. Get hotels by star rating
    print("\n6. HOTELS BY STAR RATING")
    get_hotels_by_star_rating(3, 5, limit=5)
    
    # 7. Check field existence
    print("\n7. FIELD EXISTENCE CHECK")
    check_field_existence("properties.stars")
    check_field_existence("properties.website")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main_test()