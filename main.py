# main.py (COMPLETE FIXED VERSION)
from datetime import datetime
from pprint import pprint
import os
import json
from bson import ObjectId

import folium
from folium import plugins

from connection import (
    hotels_col,
    cities_col,
    state_boundary_col,
    tourist_attractions_col
)

from crud_hotels import (
    insert_hotel, get_hotels_in_city, update_hotel_rating,
    delete_tourist_attraction, get_one_hotel, get_hotel_by_name,
    get_hotels_without_city, get_hotels_by_star_rating, delete_hotel_by_name,
    delete_hotels_without_geometry, count_hotels, check_field_existence
)

from queries import (
    nearest_city_to_point,
    nearest_city_to_attraction,
    hotels_near_attraction,
    distance_between_cities,
    attraction_buffer,
    tourist_spots_without_hotels,
    central_city_of_tn,
    nearest_hotels_to_attraction,
    list_all_attractions,
    find_attraction_by_partial_name,
    attractions_ranked_by_hotels,
    least_served_attractions,
    multi_radius_buffer_analysis,
    attraction_density_hotspots,
    hotel_density_around_cities,
    optimal_hotel_location_candidates,
    geometry_health_check,
    extract_coordinates
)

from visualize import (
    create_map,
    plot_points,
    plot_single_point,
    plot_buffer,
    visualize_attraction_context,
    plot_geojson,
    visualize_multi_radius_buffers,
    visualize_density_hotspots,
    visualize_hotel_density_cities,
    visualize_optimal_locations
)

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

def clean_document_for_json(doc):
    if not doc:
        return doc
    
    cleaned = doc.copy()
    
    if '_id' in cleaned and isinstance(cleaned['_id'], ObjectId):
        cleaned['_id'] = str(cleaned['_id'])
    
    if 'properties' in cleaned and isinstance(cleaned['properties'], dict):
        for key, value in list(cleaned['properties'].items()):
            if isinstance(value, datetime):
                cleaned['properties'][key] = value.isoformat()
            elif isinstance(value, ObjectId):
                cleaned['properties'][key] = str(value)
    
    return cleaned

def clean_documents_for_json(docs):
    return [clean_document_for_json(doc) for doc in docs]

def save_map(map_obj, filename):
    output_dir = "visualizations"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filepath = os.path.join(output_dir, filename)
    
    try:
        map_obj.save(filepath)
        print(f"Map saved to: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving map {filename}: {e}")
        return None

def find_best_attraction_to_use():
    marina_beach = tourist_attractions_col.find_one({"properties.name": "Marina Beach"})
    if marina_beach:
        print("Found 'Marina Beach' in attractions")
        return "Marina Beach", marina_beach
    
    print("\nSearching for attractions...")
    marina_attractions = find_attraction_by_partial_name("Marina")
    beach_attractions = find_attraction_by_partial_name("Beach")
    
    all_attractions = marina_attractions + beach_attractions
    
    if all_attractions:
        attraction_name = all_attractions[0]
        attraction = tourist_attractions_col.find_one({"properties.name": attraction_name})
        if attraction:
            print(f"Using attraction: {attraction_name}")
            return attraction_name, attraction
    
    print("\nListing first 10 attractions:")
    attractions_list = list_all_attractions()
    for i, name in enumerate(attractions_list[:10], 1):
        print(f"{i}. {name}")
    
    if attractions_list:
        attraction_name = attractions_list[0]
        attraction = tourist_attractions_col.find_one({"properties.name": attraction_name})
        if attraction:
            print(f"\nUsing first available attraction: {attraction_name}")
            return attraction_name, attraction
    
    print("No attractions found in database")
    return None, None

def get_hotels_for_visualization(limit=100):
    """Get hotels for visualization, cleaned for JSON serialization"""
    hotels = list(hotels_col.find({}, {
        "properties.name": 1, 
        "geometry": 1,
        "properties.district": 1,
        "properties.stars": 1,
        "properties.addr:city": 1
    }).limit(limit))
    
    return clean_documents_for_json(hotels)


def get_attractions_for_visualization(limit=50):
    """Get attractions for visualization, cleaned for JSON serialization"""
    attractions = list(tourist_attractions_col.find({}, {
        "properties.name": 1,
        "geometry": 1,
        "properties.tourism": 1
    }).limit(limit))
    
    return clean_documents_for_json(attractions)

def main():
    if not os.path.exists("visualizations"):
        os.makedirs("visualizations")
    
    print("=" * 60)
    print("HOTEL MANAGEMENT SYSTEM - SPATIAL ANALYSIS")
    print("=" * 60)
    
    print("\n" + "=" * 60)
    print("DATA AVAILABILITY CHECK")
    print("=" * 60)
    
    print(f"\nHotels: {hotels_col.count_documents({})}")
    print(f"Cities: {cities_col.count_documents({})}")
    print(f"Tourist Attractions: {tourist_attractions_col.count_documents({})}")
    print(f"State Boundary: {state_boundary_col.count_documents({})}")
    
    attraction_name, attraction_doc = find_best_attraction_to_use()
    
    print("\n" + "=" * 60)
    print("CRUD OPERATIONS")
    print("=" * 60)
    
    print("\n----- BASIC STATS -----")
    total_hotels = count_hotels()
    
    print("\n----- READ ONE HOTEL -----")
    sample_hotel = get_one_hotel()
    
    print("\n----- READ HOTEL BY NAME -----")
    sample_hotel_name = "Raintree"
    chola_hotel = get_hotel_by_name(sample_hotel_name)
    if not chola_hotel:
        any_hotel = hotels_col.find_one({}, {"properties.name": 1})
        if any_hotel and "properties" in any_hotel:
            sample_hotel_name = any_hotel["properties"].get("name", "Test Hotel")
            print(f"Using hotel: {sample_hotel_name}")
    
    print("\n----- READ HOTELS IN CITY -----")
    chennai_hotels = get_hotels_in_city("Chennai")
    print(f"Found {len(chennai_hotels)} hotels in Chennai")
    
    if chennai_hotels:
        m1 = create_map(13.0827, 80.2707, 12)
        plot_points(m1, clean_documents_for_json(chennai_hotels), popup_field="name", color="blue", radius=6)
        save_map(m1, "01_chennai_hotels.html")
        print("Visualization 1: Chennai hotels map created")
    else:
        print("No hotels found in Chennai")
    
    print("\n----- READ HOTELS WITHOUT CITY -----")
    missing_city = get_hotels_without_city()
    print(f"Found {len(missing_city)} hotels without city info")
    
    if missing_city:
        m2 = create_map(11.1271, 78.6569, 7)
        plot_points(m2, clean_documents_for_json(missing_city), popup_field="name", color="orange", radius=6)
        save_map(m2, "02_hotels_without_city.html")
        print("Visualization 2: Hotels without city info map created")
    
    print("\n----- READ HOTELS BY STAR RATING -----")
    high_star_hotels = get_hotels_by_star_rating(4)
    print(f"Found {len(high_star_hotels)} hotels with 4+ stars")
    
    if high_star_hotels:
        m3 = create_map(11.1271, 78.6569, 7)
        plot_points(m3, clean_documents_for_json(high_star_hotels), popup_field="name", color="gold", radius=6)
        save_map(m3, "03_high_star_hotels.html")
        print("Visualization 3: High-star hotels map created")
    
    print("\n----- FIELD EXISTENCE CHECK -----")
    stars_count = check_field_existence("properties.stars")
    website_count = check_field_existence("properties.website")
    
    print("\n----- INSERT NEW HOTEL -----")
    sample_hotel = {
        "type": "Feature",
        "properties": {
            "name": "Demo Residency",
            "tourism": "hotel",
            "stars": 3,
            "addr:city": "Chennai",
            "website": "https://demoresidency.example"
        },
        "geometry": {
            "type": "Point",
            "coordinates": [80.2710, 13.0825]
        }
    }
    insert_hotel(sample_hotel)
    
    print("\n----- UPDATE HOTEL RATING -----")
    update_hotel_rating("Demo Residency", 4)
    
    print("\n----- VERIFY UPDATE -----")
    demo_hotel = get_hotel_by_name("Demo Residency")
    
    print("\n----- DELETE HOTEL -----")
    delete_hotel_by_name("Demo Residency")
    
    print("\n----- DELETE ATTRACTION (IF EXISTS) -----")
    delete_tourist_attraction("Obsolete Monument")
    
    print("\n----- DELETE INVALID HOTELS -----")
    delete_hotels_without_geometry()
    
    print("\n----- FINAL HOTEL COUNT -----")
    final_count = count_hotels()
    
    print("\n" + "=" * 60)
    print("CORE SPATIAL QUERIES")
    print("=" * 60)
    
    print("\n1. NEAREST CITY TO POINT (80.2707, 13.0827)")
    result_1 = nearest_city_to_point(80.2707, 13.0827)
    pprint(result_1)
    
    m4 = create_map(13.0827, 80.2707, 12)
    folium.CircleMarker(
        location=[13.0827, 80.2707],
        radius=8,
        color="red",
        fill=True,
        popup="Reference Point (13.0827, 80.2707)"
    ).add_to(m4)
    
    if result_1:
        nearest_city_name = result_1[0].get("properties", {}).get("name")
        if nearest_city_name:
            nearest_city = cities_col.find_one({"properties.name": nearest_city_name})
            if nearest_city:
                plot_single_point(m4, clean_document_for_json(nearest_city), popup_field="name", color="green", radius=8)
    
    save_map(m4, "04_nearest_city_to_point.html")
    print("Visualization 4: Nearest city to point map created")
    
    if attraction_name:
        print(f"\n2. NEAREST CITY TO ATTRACTION ({attraction_name})")
        result_2 = nearest_city_to_attraction(attraction_name)
        pprint(result_2)
    else:
        print("\n2. NEAREST CITY TO ATTRACTION")
        print("No attraction available to query")
    
    print("\n3. DISTANCE FROM CHENNAI TO OTHER CITIES")
    result_3 = distance_between_cities("Chennai")
    print(f"Calculated distances to {len(result_3)-1 if result_3 else 0} other cities")
    if result_3:
        pprint(result_3[:5])
    
    if result_3 and len(result_3) > 0:
        m3b = create_map(13.0827, 80.2707, 7)
        chennai_city = cities_col.find_one({"properties.name": "Chennai"})
        if chennai_city:
            plot_single_point(m3b, clean_document_for_json(chennai_city), popup_field="name", color="red", radius=10)
        
        for city_data in result_3[1:6]:
            city_name = city_data.get("properties", {}).get("name")
            if city_name:
                city = cities_col.find_one({"properties.name": city_name})
                if city:
                    distance = city_data.get("distance_m", 0)
                    distance_km = distance / 1000 if distance else 0
                    popup_text = f"{city_name}<br>Distance: {distance_km:.1f} km"
                    
                    folium.CircleMarker(
                        location=[city["geometry"]["coordinates"][1], city["geometry"]["coordinates"][0]],
                        radius=6,
                        color="blue",
                        fill=True,
                        popup=popup_text
                    ).add_to(m3b)
        
        save_map(m3b, "03b_city_distances_from_chennai.html")
        print("Visualization 3b: City distances from Chennai map created")
    
    if attraction_name:
        print(f"\n4. HOTELS NEAR {attraction_name} (within 3km)")
        result_4 = hotels_near_attraction(attraction_name, max_km=3)
        print(f"Found {len(result_4)} hotels near {attraction_name}")
        if result_4:
            hotel_names = [h["properties"].get("name") for h in result_4[:5] if h["properties"].get("name")]
            pprint(hotel_names)
    else:
        print("\n4. HOTELS NEAR ATTRACTION")
        print("No attraction available to query")
    
    if attraction_doc and result_4:
        m4b = visualize_attraction_context(
            clean_document_for_json(attraction_doc), 
            nearby_hotels=clean_documents_for_json(result_4)
        )
        safe_filename = attraction_name.replace(' ', '_').replace(':', '_').lower()
        save_map(m4b, f"04b_hotels_near_{safe_filename}.html")
        print(f"Visualization 4b: Hotels near {attraction_name} map created")
    elif attraction_doc:
        print(f"No hotels found near {attraction_name}")
    
    print("\n5. TOURIST SPOTS WITHOUT NEARBY HOTELS (within 3km)")
    result_5 = tourist_spots_without_hotels(radius_km=3)
    print(f"Found {len(result_5)} tourist spots without nearby hotels")
    
    if result_5:
        m5 = create_map(11.1271, 78.6569, 7)
        plot_points(m5, clean_documents_for_json(result_5), popup_field="name", color="red", radius=6)
        save_map(m5, "05_tourist_spots_without_hotels.html")
        print("Visualization 5: Tourist spots without hotels map created")
    
    print("\n" + "=" * 60)
    print("NEW SPATIAL ANALYSIS QUERIES")
    print("=" * 60)
    
    print("\n6. ATTRACTIONS RANKED BY NUMBER OF NEARBY HOTELS (3km)")
    result_6 = attractions_ranked_by_hotels(max_km=3)
    print(f"Ranked {len(result_6)} attractions")
    if result_6:
        print("\nTop 10 attractions with most nearby hotels:")
        for i, att in enumerate(result_6[:10], 1):
            print(f"{i}. {att['name']}: {att['hotel_count']} hotels")
    
    if result_6:
        m6 = create_map(11.1271, 78.6569, 7)
        for i, att in enumerate(result_6[:20]):
            if att.get("coordinates") and len(att["coordinates"]) >= 2:
                folium.CircleMarker(
                    location=[att["coordinates"][1], att["coordinates"][0]],
                    radius=5 + (att["hotel_count"] * 0.5),
                    color="green" if att["hotel_count"] > 5 else "orange" if att["hotel_count"] > 2 else "red",
                    fill=True,
                    popup=f"{att['name']}<br>Nearby hotels: {att['hotel_count']}"
                ).add_to(m6)
        save_map(m6, "06_attractions_ranked_by_hotels.html")
        print("Visualization 6: Attractions ranked by hotels map created")
    
    print("\n7. LEAST-SERVED TOURIST ATTRACTIONS (0-1 hotels within 3km)")
    result_7 = least_served_attractions(max_km=3, max_hotels=1)
    print(f"Found {len(result_7)} least-served attractions")
    if result_7:
        print("\nFirst 10 least-served attractions:")
        for i, att in enumerate(result_7[:10], 1):
            print(f"{i}. {att['name']}: {att['hotel_count']} hotels")
    
    if result_7:
        m7 = create_map(11.1271, 78.6569, 7)
        for att in result_7[:30]:
            if att.get("coordinates") and len(att["coordinates"]) >= 2:
                folium.CircleMarker(
                    location=[att["coordinates"][1], att["coordinates"][0]],
                    radius=8,
                    color="red",
                    fill=True,
                    popup=f"{att['name']}<br>Nearby hotels: {att['hotel_count']}"
                ).add_to(m7)
        save_map(m7, "07_least_served_attractions.html")
        print("Visualization 7: Least-served attractions map created")
    
    if attraction_name:
        print(f"\n8. MULTI-RADIUS BUFFER ANALYSIS AROUND {attraction_name}")
        result_8 = multi_radius_buffer_analysis(attraction_name)
        if result_8:
            print(f"Buffer analysis for {attraction_name}:")
            for radius in ["1_km", "3_km", "5_km"]:
                print(f"  {radius}: {result_8[radius]} hotels")
        
        if attraction_doc:
            m8 = visualize_multi_radius_buffers(attraction_doc)
            safe_filename = attraction_name.replace(' ', '_').replace(':', '_').lower()
            save_map(m8, f"08_multi_radius_{safe_filename}.html")
            print(f"Visualization 8: Multi-radius buffer analysis for {attraction_name}")
    
    print("\n9. ATTRACTION DENSITY HOTSPOTS (5km radius)")
    result_9 = attraction_density_hotspots(radius_km=5)
    print(f"Analyzed {len(result_9)} attraction hotspots")
    if result_9:
        print("\nTop 10 attraction density hotspots:")
        for i, hotspot in enumerate(result_9[:10], 1):
            print(f"{i}. {hotspot['name']}: {hotspot['density_count']} nearby attractions")
    
    if result_9:
        m9 = visualize_density_hotspots(result_9)
        save_map(m9, "09_attraction_density_hotspots.html")
        print("Visualization 9: Attraction density hotspots map created")
    
    print("\n10. HOTEL DENSITY AROUND CITIES (5km radius)")
    result_10 = hotel_density_around_cities(radius_km=5)
    print(f"Analyzed {len(result_10)} cities")
    if result_10:
        print("\nTop 10 cities by hotel density:")
        for i, city in enumerate(result_10[:10], 1):
            print(f"{i}. {city['city']}: {city['hotel_count']} hotels")
    
    if result_10:
        m10 = visualize_hotel_density_cities(result_10)
        save_map(m10, "10_hotel_density_cities.html")
        print("Visualization 10: Hotel density around cities map created")
    
    print("\n11. CENTRAL CITY OF TAMIL NADU")
    result_11 = central_city_of_tn()
    
    if result_11:
        city_name = result_11[0].get("properties", {}).get("name")
        coords = result_11[0].get("coordinates")
        
        if city_name and coords and len(coords) >= 2:
            print(f"Central city: {city_name}")
            print(f"Coordinates: {coords[0]:.4f}, {coords[1]:.4f}")
            
            central_city = cities_col.find_one({"properties.name": city_name})
            
            if central_city:
                m11 = create_map(11.1271, 78.6569, 7)
                
                plot_single_point(m11, clean_document_for_json(central_city), 
                                 popup_field="name", color="green", radius=10)
                
                state = state_boundary_col.find_one()
                if state:
                    plot_geojson(m11, clean_document_for_json(state), color="gray")
                
                save_map(m11, "11_central_city_tn.html")
                print("Visualization 11: Central city of Tamil Nadu map created")
            else:
                print(f"Could not find city document for {city_name}")
        else:
            print("Central city found but has invalid data")
            pprint(result_11)
    else:
        print("No central city found")
    
    if attraction_name:
        print(f"\n12. 5 NEAREST HOTELS TO {attraction_name}")
        result_12 = nearest_hotels_to_attraction(attraction_name, k=5)
        print("Nearest hotels:")
        for i, hotel in enumerate(result_12, 1):
            name = hotel["properties"].get("name", "Unnamed Hotel")
            print(f"{i}. {name}")
    else:
        print("\n12. NEAREST HOTELS TO ATTRACTION")
        print("No attraction available to query")
    
    if attraction_doc and result_12:
        m12 = visualize_attraction_context(
            clean_document_for_json(attraction_doc), 
            nearby_hotels=clean_documents_for_json(result_12)
        )
        safe_filename = attraction_name.replace(' ', '_').replace(':', '_').lower()
        save_map(m12, f"12_nearest_hotels_to_{safe_filename}.html")
        print(f"Visualization 12: Nearest hotels to {attraction_name} map created")
    
    print("\n13. OPTIMAL HOTEL LOCATION CANDIDATES")
    result_13 = optimal_hotel_location_candidates()
    print(f"Analyzed {len(result_13)} candidate locations")
    if result_13:
        print("\nTop 10 optimal hotel location candidates:")
        for i, candidate in enumerate(result_13[:10], 1):
            print(f"{i}. {candidate['name']}: Score {candidate['score']:.2f}")
            print(f"   Attraction Density: {candidate['attraction_density']}")
            print(f"   Hotel Density: {candidate['hotel_density']}")
            print(f"   Distance to City: {candidate['distance_to_city_km']:.1f} km")
    
    if result_13:
        m13 = visualize_optimal_locations(result_13)
        save_map(m13, "13_optimal_hotel_locations.html")
        print("Visualization 13: Optimal hotel location candidates map created")
    
    print("\n14. LIST ALL TOURIST ATTRACTIONS")
    all_attractions_list = list_all_attractions()
    print(f"Total attractions available: {len(all_attractions_list)}")
    print("\nFirst 20 attractions:")
    for i, name in enumerate(all_attractions_list[:20], 1):
        print(f"{i}. {name}")
    
    print("\n15. GEOMETRY HEALTH CHECK")
    result_15 = geometry_health_check()
    print("Geometry validation results:")
    for collection, stats in result_15.items():
        valid_pct = (stats["valid"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {collection}: {stats['valid']}/{stats['total']} valid ({valid_pct:.1f}%)")
    
    print("\n" + "=" * 60)
    print("SUMMARY VISUALIZATIONS")
    print("=" * 60)
    
    all_hotels = ()
    if all_hotels:
        m_summary = create_map(11.1271, 78.6569, 7)
        plot_points(m_summary, all_hotels, popup_field="name", color="blue", radius=4)
        
        state = state_boundary_col.find_one()
        if state:
            plot_geojson(m_summary, clean_document_for_json(state), color="gray")
        
        save_map(m_summary, "summary_all_hotels_tn.html")
        print("Summary: All hotels in Tamil Nadu map created")
    
    all_attractions = get_attractions_for_visualization(limit=50)
    
    if all_attractions:
        m_attractions = create_map(11.1271, 78.6569, 7)
        plot_points(m_attractions, all_attractions, popup_field="name", color="red", radius=5)
        
        if all_hotels:
            plot_points(m_attractions, all_hotels[:50], popup_field="name", color="blue", radius=3)
        
        if state:
            plot_geojson(m_attractions, clean_document_for_json(state), color="gray")
        
        save_map(m_attractions, "summary_attractions_and_hotels.html")
        print("Summary: Attractions and hotels distribution map created")
    
    print("\n" + "=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    
    pipeline = [
        {"$match": {"properties.addr:city": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$properties.addr:city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    top_cities = list(hotels_col.aggregate(pipeline))
    print("\nTop 10 Cities by Hotel Count:")
    for city in top_cities:
        print(f"  {city['_id']}: {city['count']} hotels")
    
    attraction_types = tourist_attractions_col.distinct("properties.tourism")
    print(f"\nAttraction types: {attraction_types}")
    
    print("\n" + "=" * 60)
    print("VISUALIZATION SUMMARY")
    print("=" * 60)
    print("The following maps have been created in the 'visualizations' folder:")
    
    visualization_files = []
    vis_counter = 1
    
    if chennai_hotels:
        print(f"{vis_counter}. 01_chennai_hotels.html - Hotels in Chennai")
        vis_counter += 1
        visualization_files.append("01_chennai_hotels.html")
    
    if missing_city:
        print(f"{vis_counter}. 02_hotels_without_city.html - Hotels missing city info")
        vis_counter += 1
        visualization_files.append("02_hotels_without_city.html")
    
    if high_star_hotels:
        print(f"{vis_counter}. 03_high_star_hotels.html - Hotels with 4+ stars")
        vis_counter += 1
        visualization_files.append("03_high_star_hotels.html")
    
    print(f"{vis_counter}. 04_nearest_city_to_point.html - Nearest city to reference point")
    vis_counter += 1
    visualization_files.append("04_nearest_city_to_point.html")
    
    if result_3:
        print(f"{vis_counter}. 03b_city_distances_from_chennai.html - City distances from Chennai")
        vis_counter += 1
        visualization_files.append("03b_city_distances_from_chennai.html")
    
    if attraction_doc and result_4:
        safe_name = attraction_name.replace(' ', '_').replace(':', '_').lower()
        print(f"{vis_counter}. 04b_hotels_near_{safe_name}.html - Hotels near {attraction_name}")
        vis_counter += 1
        visualization_files.append(f"04b_hotels_near_{safe_name}.html")
    
    if result_5:
        print(f"{vis_counter}. 05_tourist_spots_without_hotels.html - Tourist spots lacking hotels")
        vis_counter += 1
        visualization_files.append("05_tourist_spots_without_hotels.html")
    
    if result_6:
        print(f"{vis_counter}. 06_attractions_ranked_by_hotels.html - Attractions ranked by nearby hotels")
        vis_counter += 1
        visualization_files.append("06_attractions_ranked_by_hotels.html")
    
    if result_7:
        print(f"{vis_counter}. 07_least_served_attractions.html - Least-served tourist attractions")
        vis_counter += 1
        visualization_files.append("07_least_served_attractions.html")
    
    if attraction_doc:
        safe_name = attraction_name.replace(' ', '_').replace(':', '_').lower()
        print(f"{vis_counter}. 08_multi_radius_{safe_name}.html - Multi-radius buffer analysis")
        vis_counter += 1
        visualization_files.append(f"08_multi_radius_{safe_name}.html")
    
    if result_9:
        print(f"{vis_counter}. 09_attraction_density_hotspots.html - Attraction density hotspots")
        vis_counter += 1
        visualization_files.append("09_attraction_density_hotspots.html")
    
    if result_10:
        print(f"{vis_counter}. 10_hotel_density_cities.html - Hotel density around cities")
        vis_counter += 1
        visualization_files.append("10_hotel_density_cities.html")
    
    if result_11 and result_11[0].get("properties", {}).get("name"):
        print(f"{vis_counter}. 11_central_city_tn.html - Central city of Tamil Nadu")
        vis_counter += 1
        visualization_files.append("11_central_city_tn.html")
    
    if attraction_doc and result_12:
        safe_name = attraction_name.replace(' ', '_').replace(':', '_').lower()
        print(f"{vis_counter}. 12_nearest_hotels_to_{safe_name}.html - 5 nearest hotels to {attraction_name}")
        vis_counter += 1
        visualization_files.append(f"12_nearest_hotels_to_{safe_name}.html")
    
    if result_13:
        print(f"{vis_counter}. 13_optimal_hotel_locations.html - Optimal hotel location candidates")
        vis_counter += 1
        visualization_files.append("13_optimal_hotel_locations.html")
    
    if all_hotels:
        print(f"{vis_counter}. summary_all_hotels_tn.html - All hotels in Tamil Nadu")
        vis_counter += 1
        visualization_files.append("summary_all_hotels_tn.html")
    
    if all_attractions:
        print(f"{vis_counter}. summary_attractions_and_hotels.html - Attractions and hotels distribution")
        vis_counter += 1
        visualization_files.append("summary_attractions_and_hotels.html")
    
    print(f"\nTotal visualizations created: {vis_counter - 1}")
    
    created_files = []
    for file in visualization_files:
        filepath = os.path.join("visualizations", file)
        if os.path.exists(filepath):
            created_files.append(file)
    
    print(f"Files actually saved: {len(created_files)}")
    print("=" * 60)
    
    print("\nPROCESS COMPLETED SUCCESSFULLY!")
    print(f"Total hotels in database: {final_count}")
    print(f"Visualizations saved to: {os.path.abspath('visualizations')}")
    print("\nTo view the maps, open the HTML files in any web browser.")

if __name__ == "__main__":
    main()