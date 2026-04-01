# GeoSpatial Tourism Analytics Engine

A Python-based tool for analyzing tourism data and hotel distribution across Tamil Nadu using MongoDB and GeoJSON.

---

## What This Does

The project runs location-based queries on a dataset of tourist attractions, hotels, and cities in Tamil Nadu. It helps answer practical questions like which areas have no hotels nearby, where hotel density is high, and which locations make sense for new hotel investment.

---

## Tech Stack

- Python
- MongoDB
- PyMongo
- Shapely
- GeoJSON

---

## How Spatial Data is Stored

All locations are stored as GeoJSON points:

```json
{
  "type": "Point",
  "coordinates": [longitude, latitude]
}
```

A `2dsphere` index is created on each collection to enable distance and radius queries:

```python
hotels_col.create_index([("geometry", "2dsphere")])
```

---

## Spatial Operators Used

| Operator | What It Does |
|---|---|
| $geoNear | Finds the nearest location and returns the distance |
| $near | Returns nearby points sorted by distance |
| $geoWithin | Checks if a point falls within a shape |
| $centerSphere | Runs circular radius queries |

---

## Project Structure

```
.
├── connection.py          # Sets up MongoDB collections
├── geospatial_queries.py  # All query and analysis functions
├── README.md
```

---

## Functions

### Finding Nearby Locations

**nearest_city_to_point(lon, lat)**
Returns the closest city to a given coordinate.

**nearest_city_to_attraction(attraction_name)**
Returns the closest city to a named tourist attraction.

### Hotel Queries

**hotels_near_attraction(attraction_name, max_km)**
Returns all hotels within a set distance from an attraction.

**nearest_hotels_to_attraction(attraction_name, k)**
Returns the top K closest hotels to an attraction.

**count_hotels_near_point(coords, radius_km)**
Counts hotels within a circular area.

### Distance and Geometry

**haversine_distance(lon1, lat1, lon2, lat2)**
Calculates straight-line distance between two coordinates on the earth's surface.

**attraction_buffer(attraction_name, km)**
Creates a circular polygon around an attraction at a given radius.

### Gap and Density Analysis

**tourist_spots_without_hotels(radius_km)**
Finds attractions that have no hotels within the given radius. Useful for spotting underserved areas.

**attractions_ranked_by_hotels()**
Ranks all attractions by how many hotels are nearby.

**least_served_attractions()**
Returns attractions with the fewest hotel options nearby.

**multi_radius_buffer_analysis()**
Runs hotel density checks at 1km, 3km, and 5km from each attraction.

### Advanced Analysis

**attraction_density_hotspots(radius_km)**
Finds areas with clusters of tourist attractions close together.

**hotel_density_around_cities(radius_km)**
Ranks cities by the number of hotels around them.

### Location Recommendation

**optimal_hotel_location_candidates()**

Scores potential hotel locations based on three factors:

- Number of nearby attractions (positive signal)
- Existing hotel competition (negative signal)
- Distance from the nearest city (negative signal)

The output can be used to prioritize where a new hotel would have the most impact.

### Data Quality

**geometry_health_check()**
Checks all records for valid coordinate data before running queries.

---

## Example Usage

```python
# Hotels within 3km of a specific attraction
hotels = hotels_near_attraction("Meenakshi Temple", 3)

# Top 5 closest hotels to a location
nearest = nearest_hotels_to_attraction("Ooty Lake", 5)

# Attractions with no hotels nearby
gaps = tourist_spots_without_hotels(3)

# Scored list of good locations for a new hotel
candidates = optimal_hotel_location_candidates()
```

---

## Notes

- Coordinates must always be in [longitude, latitude] order, not [latitude, longitude]
- The 2dsphere index must exist on each collection before running queries
- Run geometry_health_check() if you are loading new data to catch any invalid records early

---

## Possible Improvements

- Add map visualization using Folium or Mapbox
- Build a REST API layer using FastAPI
- Add ML-based demand prediction for hotel placement
- Set up a pipeline for real-time data updates

---

## Author

- Anandika M
- Farhana S
