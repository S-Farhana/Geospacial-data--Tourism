# visualize.py (COMPLETE IMPROVED VERSION)
import folium
from shapely.geometry import shape
import json
from bson import ObjectId
from datetime import datetime


def clean_for_visualization(feature):
    """Clean a feature for visualization - keep essential fields"""
    if not feature:
        return feature
    
    cleaned = feature.copy()
    
    # Keep _id as string for reference
    if '_id' in cleaned and isinstance(cleaned['_id'], ObjectId):
        cleaned['_id'] = str(cleaned['_id'])
    
    # Clean properties - remove None values, keep important ones
    if 'properties' in cleaned and isinstance(cleaned['properties'], dict):
        # Create a new properties dict with only non-None values
        new_props = {}
        for key, value in cleaned['properties'].items():
            if value is not None and str(value).strip() != '':
                if isinstance(value, (ObjectId, datetime)):
                    new_props[key] = str(value)
                else:
                    new_props[key] = value
        
        # Always ensure name exists
        if 'name' not in new_props:
            # Try to get name from various possible fields
            name_fields = ['name', 'Name', 'NAME', 'title', 'Title', 'TITLE']
            for field in name_fields:
                if field in cleaned['properties'] and cleaned['properties'][field]:
                    new_props['name'] = str(cleaned['properties'][field])
                    break
            else:
                new_props['name'] = 'Unnamed Location'
        
        cleaned['properties'] = new_props
    elif 'properties' not in cleaned:
        # Ensure properties dict exists
        cleaned['properties'] = {'name': 'Unnamed Location'}
    
    return cleaned


def clean_features_for_visualization(features):
    """Clean a list of features"""
    cleaned_features = []
    for feature in features:
        if feature:
            cleaned = clean_for_visualization(feature)
            if cleaned:
                cleaned_features.append(cleaned)
    return cleaned_features


def extract_coordinates_for_viz(geometry):
    """Safely extract coordinates from geometry for visualization"""
    if not geometry or "coordinates" not in geometry:
        return None
    
    coords = geometry["coordinates"]
    
    # Handle deeply nested arrays
    def extract_numeric_value(val, depth=0, max_depth=10):
        if depth > max_depth:
            return None
        
        if isinstance(val, (int, float)):
            return float(val)
        elif isinstance(val, list) and len(val) > 0:
            # Try first element
            result = extract_numeric_value(val[0], depth + 1, max_depth)
            if result is not None:
                return result
            # If first didn't work, try to find any numeric in the list
            for item in val:
                result = extract_numeric_value(item, depth + 1, max_depth)
                if result is not None:
                    return result
        return None
    
    # Extract longitude (first value)
    lon = extract_numeric_value(coords)
    if lon is None:
        return None
    
    # Extract latitude (second value or same as lon)
    lat = None
    if isinstance(coords, list) and len(coords) > 1:
        lat = extract_numeric_value(coords[1])
    
    if lat is None:
        # Some might have only one coordinate or lat in a different position
        # Try to find second numeric value anywhere
        def find_second_numeric(val, first_found=False, depth=0, max_depth=10):
            if depth > max_depth:
                return None
            
            if isinstance(val, (int, float)):
                if first_found:
                    return float(val)
                else:
                    return None, True  # Found first, continue looking
            
            elif isinstance(val, list):
                for item in val:
                    result = find_second_numeric(item, first_found, depth + 1, max_depth)
                    if isinstance(result, tuple) and len(result) == 2:
                        if result[0] is not None:
                            return result[0]
                        first_found = result[1]
                    elif result is not None:
                        return result
            return None
        
        lat = find_second_numeric(coords, False, 0, 10)
    
    # If still no latitude, use longitude (points with same coords)
    if lat is None:
        lat = lon
    
    # Validate coordinates are within reasonable bounds
    if abs(lon) > 180 or abs(lat) > 90:
        print(f"Warning: Invalid coordinates: lon={lon}, lat={lat}")
        return None
    
    return [lon, lat]


def create_map(center_lat=13.0827, center_lon=80.2707, zoom=7, tiles='OpenStreetMap'):
    """Create a base map with specified tiles"""
    return folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=zoom,
        tiles=tiles,
        control_scale=True
    )


def plot_geojson(map_obj, geojson_obj, popup_field=None, color="blue", weight=2, fill_opacity=0.3):
    """Plot GeoJSON with better styling"""
    if not geojson_obj:
        print("Warning: No GeoJSON data to plot")
        return
    
    # Create style function
    def style_function(feature):
        return {
            "color": color,
            "weight": weight,
            "fillOpacity": fill_opacity,
            "fillColor": color
        }
    
    # Create popup
    def popup_function(feature):
        props = feature.get('properties', {})
        if not props:
            return "Area"
        
        # Find a name field
        name_fields = ['name', 'Name', 'NAME', 'title', 'Title']
        for field in name_fields:
            if field in props and props[field]:
                return f"<b>{props[field]}</b>"
        
        # If popup_field specified, use it
        if popup_field and popup_field in props and props[popup_field]:
            return f"<b>{props[popup_field]}</b>"
        
        # Show first few properties
        lines = []
        for key, value in list(props.items())[:3]:
            if value:
                lines.append(f"<b>{key}:</b> {value}")
        
        if lines:
            return "<br>".join(lines)
        else:
            return "Area"
    
    try:
        # Add GeoJSON to map
        folium.GeoJson(
            geojson_obj,
            style_function=style_function,
            popup=folium.GeoJsonPopup(fields=['name'] if 'name' in geojson_obj.get('properties', {}) else []),
            tooltip=folium.GeoJsonTooltip(fields=['name'] if 'name' in geojson_obj.get('properties', {}) else [])
        ).add_to(map_obj)
    except Exception as e:
        print(f"Error plotting GeoJSON: {e}")


def plot_points(map_obj, features, popup_field=None, color="blue", radius=4, tooltip_field=None):
    """Plot multiple points on map with better popups"""
    if not features:
        print("Warning: No features to plot")
        return
    
    cleaned_features = clean_features_for_visualization(features)
    if not cleaned_features:
        print("Warning: All features failed cleaning")
        return
    
    print(f"Plotting {len(cleaned_features)} cleaned features")
    
    for i, feature in enumerate(cleaned_features):
        if not feature or 'geometry' not in feature:
            print(f"Warning: Feature {i} has no geometry")
            continue
        
        coords = extract_coordinates_for_viz(feature['geometry'])
        if not coords or len(coords) < 2:
            print(f"Warning: Feature {i} has invalid coordinates: {feature.get('geometry', {}).get('coordinates')}")
            continue
        
        lat, lon = coords[1], coords[0]
        
        # Get properties for popup
        props = feature.get('properties', {})
        
        # Create informative popup
        popup_lines = []
        
        # Try to get name
        name = props.get('name', 'Unnamed Location')
        popup_lines.append(f"<h4 style='margin: 0 0 10px 0;'>{name}</h4>")
        
        # Add other properties (excluding name and _id)
        for key, value in props.items():
            if key not in ['name', '_id'] and value and str(value).strip():
                popup_lines.append(f"<b>{key}:</b> {value}")
        
        if len(popup_lines) <= 1:  # Only has name
            popup_lines.append("No additional information available")
        
        popup_text = "<br>".join(popup_lines)
        
        # Create tooltip
        tooltip_text = name
        if tooltip_field and tooltip_field in props and props[tooltip_field]:
            tooltip_text = f"{name} - {props[tooltip_field]}"
        
        # Create marker with popup
        try:
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                color=color,
                fill=True,
                fill_opacity=0.8,
                fill_color=color,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=tooltip_text
            ).add_to(map_obj)
        except Exception as e:
            print(f"Error plotting point {i}: {e}")


def plot_single_point(map_obj, feature, popup_field=None, color="red", radius=6, tooltip=None):
    """Plot a single point with detailed popup"""
    cleaned_feature = clean_for_visualization(feature)
    
    if not cleaned_feature or 'geometry' not in cleaned_feature:
        print("Warning: Cannot plot single point - invalid feature")
        return
    
    coords = extract_coordinates_for_viz(cleaned_feature['geometry'])
    if not coords or len(coords) < 2:
        print(f"Warning: Invalid coordinates for single point: {cleaned_feature.get('geometry', {}).get('coordinates')}")
        return
    
    lat, lon = coords[1], coords[0]
    
    # Get properties
    props = cleaned_feature.get('properties', {})
    
    # Create detailed popup
    popup_lines = []
    
    # Add name
    name = props.get('name', 'Location')
    popup_lines.append(f"<h4 style='margin: 0 0 10px 0; color: #333;'>{name}</h4>")
    
    # Add other properties in a table format
    table_rows = []
    for key, value in props.items():
        if key != 'name' and value and str(value).strip():
            table_rows.append(f"""
            <tr>
                <td style="padding: 4px; border-bottom: 1px solid #eee; text-align: left;"><b>{key}</b></td>
                <td style="padding: 4px; border-bottom: 1px solid #eee; text-align: right;">{value}</td>
            </tr>
            """)
    
    if table_rows:
        popup_lines.append("""
        <div style="font-family: Arial, sans-serif; font-size: 12px;">
            <table style="border-collapse: collapse; width: 100%;">
        """ + "\n".join(table_rows) + """
            </table>
        </div>
        """)
    else:
        popup_lines.append("<p><i>No additional information available</i></p>")
    
    popup_text = "".join(popup_lines)
    
    # Create tooltip
    tooltip_text = tooltip if tooltip else name
    
    # Create marker
    try:
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_opacity=0.9,
            fill_color=color,
            popup=folium.Popup(popup_text, max_width=400),
            tooltip=tooltip_text
        ).add_to(map_obj)
    except Exception as e:
        print(f"Error plotting single point: {e}")


def plot_buffer(map_obj, buffer_geojson, color="purple", tooltip="Buffer Zone"):
    """Plot buffer zone"""
    if not buffer_geojson:
        print("Warning: No buffer GeoJSON to plot")
        return
    
    try:
        folium.GeoJson(
            buffer_geojson,
            style_function=lambda x: {
                "color": color,
                "weight": 2,
                "fillOpacity": 0.2,
                "fillColor": color
            },
            tooltip=tooltip
        ).add_to(map_obj)
    except Exception as e:
        print(f"Error plotting buffer: {e}")


def plot_gap_locations(map_obj, gap_features):
    """Plot gap locations (tourist spots without hotels)"""
    plot_points(
        map_obj,
        gap_features,
        popup_field="name",
        color="red",
        radius=6,
        tooltip_field="name"
    )


def visualize_attraction_context(attraction, nearby_hotels=None, nearest_city=None):
    """Create map showing attraction with nearby hotels and city"""
    if not attraction or 'geometry' not in attraction:
        print("Warning: Invalid attraction for context visualization")
        return create_map()
    
    coords = extract_coordinates_for_viz(attraction['geometry'])
    if not coords:
        print("Warning: Invalid coordinates for attraction")
        return create_map()
    
    lat, lon = coords[1], coords[0]
    m = create_map(center_lat=lat, center_lon=lon, zoom=14)
    
    # Add title
    attraction_name = attraction.get('properties', {}).get('name', 'Attraction')
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 300px; height: 40px; 
                background-color: white; z-index: 9999; padding: 10px;
                border: 2px solid grey; border-radius: 5px;">
        <b>{attraction_name}</b><br>
        Context Map
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Plot attraction
    plot_single_point(m, attraction, popup_field="name", color="red", radius=10, 
                      tooltip=f"Attraction: {attraction_name}")
    
    # Plot nearby hotels
    if nearby_hotels:
        print(f"Plotting {len(nearby_hotels)} nearby hotels")
        plot_points(m, nearby_hotels, popup_field="name", color="blue", radius=6,
                   tooltip_field="name")
    else:
        print("No nearby hotels to plot")
    
    # Plot nearest city
    if nearest_city:
        plot_single_point(m, nearest_city, popup_field="name", color="green", radius=8,
                         tooltip="Nearest City")
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 150px; height: 120px;
                background-color: white; z-index: 9999; padding: 10px;
                border: 2px solid grey; border-radius: 5px; font-size: 12px;">
        <b>Legend</b><br>
        <span style="color: red;">● Attraction</span><br>
        <span style="color: blue;">● Hotels</span><br>
        <span style="color: green;">● Nearest City</span>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m


def visualize_multi_radius_buffers(attraction, radii_km=[1, 3, 5], colors=["yellow", "orange", "red"]):
    """Visualize multiple buffer radii around attraction"""
    if not attraction or 'geometry' not in attraction:
        print("Warning: Invalid attraction for buffer visualization")
        return create_map()
    
    coords = extract_coordinates_for_viz(attraction['geometry'])
    if not coords:
        print("Warning: Invalid coordinates for attraction")
        return create_map()
    
    lat, lon = coords[1], coords[0]
    m = create_map(center_lat=lat, center_lon=lon, zoom=13)
    
    # Add title
    attraction_name = attraction.get('properties', {}).get('name', 'Attraction')
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 350px; height: 60px; 
                background-color: white; z-index: 9999; padding: 10px;
                border: 2px solid grey; border-radius: 5px;">
        <b>{attraction_name}</b><br>
        Multi-Radius Buffer Analysis
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Plot attraction
    plot_single_point(m, attraction, popup_field="name", color="purple", radius=10,
                     tooltip=f"Center: {attraction_name}")
    
    # Plot buffers
    for radius, color in zip(radii_km, colors):
        try:
            from shapely.geometry import Point
            point = Point(lon, lat)
            buffer_deg = radius / 111  # Approximate conversion (1° ≈ 111 km)
            
            buffered = point.buffer(buffer_deg)
            from shapely.geometry import mapping
            buffer_geojson = mapping(buffered)
            
            folium.GeoJson(
                buffer_geojson,
                style_function=lambda x, c=color: {
                    "color": c,
                    "weight": 2,
                    "fillOpacity": 0.1,
                    "fillColor": c
                },
                tooltip=f"{radius} km radius"
            ).add_to(m)
        except Exception as e:
            print(f"Error creating buffer for {radius}km: {e}")
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 180px; height: 150px;
                background-color: white; z-index: 9999; padding: 10px;
                border: 2px solid grey; border-radius: 5px; font-size: 12px;">
        <b>Buffer Zones</b><br>
        <span style="color: purple;">● Center Point</span><br>
        <span style="color: yellow; background-color: yellow;"> </span> 1 km radius<br>
        <span style="color: orange; background-color: orange;"> </span> 3 km radius<br>
        <span style="color: red; background-color: red;"> </span> 5 km radius
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m


def visualize_density_hotspots(hotspots_data, title="Attraction Density Hotspots"):
    """Visualize attraction density hotspots"""
    if not hotspots_data:
        print("Warning: No hotspot data to visualize")
        return create_map(11.1271, 78.6569, 7)
    
    m = create_map(11.1271, 78.6569, 7)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 300px; height: 40px; 
                background-color: white; z-index: 9999; padding: 10px;
                border: 2px solid grey; border-radius: 5px;">
        <b>{title}</b>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Find max density for scaling
    valid_hotspots = [h for h in hotspots_data if h.get("coordinates") and len(h.get("coordinates", [])) >= 2]
    densities = [h.get("density_count", 0) for h in valid_hotspots]
    max_density = max(densities) if densities else 1
    
    print(f"Visualizing {len(valid_hotspots)} valid hotspots (max density: {max_density})")
    
    for hotspot in valid_hotspots:
        coords = hotspot.get("coordinates")
        if not coords or len(coords) < 2:
            continue
        
        lat, lon = coords[1], coords[0]
        density = hotspot.get("density_count", 0)
        name = hotspot.get("name", "Unknown")
        
        # Scale radius based on density
        if max_density > 0:
            radius = 5 + (density / max_density * 25)
        else:
            radius = 10
        
        # Color based on density
        if max_density > 0:
            density_ratio = density / max_density
            if density_ratio > 0.7:
                color = "darkred"
            elif density_ratio > 0.4:
                color = "orange"
            else:
                color = "yellow"
        else:
            color = "yellow"
        
        # Create popup
        popup_text = f"""
        <div style="font-family: Arial, sans-serif;">
            <h4 style="margin: 0 0 10px 0;">{name}</h4>
            <p><b>Attraction Density:</b> {density}</p>
            <p><i>Number of nearby attractions within 5km radius</i></p>
        </div>
        """
        
        try:
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                color=color,
                fill=True,
                fill_opacity=0.6,
                fill_color=color,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{name}: Density {density}"
            ).add_to(m)
        except Exception as e:
            print(f"Error plotting hotspot {name}: {e}")
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: 120px;
                background-color: white; z-index: 9999; padding: 10px;
                border: 2px solid grey; border-radius: 5px; font-size: 12px;">
        <b>Density Legend</b><br>
        <span style="color: darkred;">● High Density</span><br>
        <span style="color: orange;">● Medium Density</span><br>
        <span style="color: yellow;">● Low Density</span><br>
        Max: {max_density} attractions
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m


def visualize_hotel_density_cities(city_densities, title="Hotel Density Around Cities"):
    """Visualize hotel density around cities"""
    if not city_densities:
        print("Warning: No city density data to visualize")
        return create_map(11.1271, 78.6569, 7)
    
    m = create_map(11.1271, 78.6569, 7)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 300px; height: 40px; 
                background-color: white; z-index: 9999; padding: 10px;
                border: 2px solid grey; border-radius: 5px;">
        <b>{title}</b>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Find max hotel count for scaling
    valid_cities = [c for c in city_densities if c.get("coordinates") and len(c.get("coordinates", [])) >= 2]
    hotel_counts = [c.get("hotel_count", 0) for c in valid_cities]
    max_hotels = max(hotel_counts) if hotel_counts else 1
    
    print(f"Visualizing {len(valid_cities)} valid cities (max hotels: {max_hotels})")
    
    for city_data in valid_cities:
        coords = city_data.get("coordinates")
        if not coords or len(coords) < 2:
            continue
        
        lat, lon = coords[1], coords[0]
        hotel_count = city_data.get("hotel_count", 0)
        city_name = city_data.get("city", "Unknown")
        
        # Scale radius based on hotel count
        if max_hotels > 0:
            radius = 5 + (hotel_count / max_hotels * 30)
        else:
            radius = 10
        
        # Color based on hotel count
        if max_hotels > 0:
            hotel_ratio = hotel_count / max_hotels
            if hotel_ratio > 0.7:
                color = "darkblue"
            elif hotel_ratio > 0.4:
                color = "blue"
            else:
                color = "lightblue"
        else:
            color = "lightblue"
        
        # Create popup
        popup_text = f"""
        <div style="font-family: Arial, sans-serif;">
            <h4 style="margin: 0 0 10px 0;">{city_name}</h4>
            <p><b>Hotels within 5km:</b> {hotel_count}</p>
            <p><i>Hotel density indicator for tourism planning</i></p>
        </div>
        """
        
        try:
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                color=color,
                fill=True,
                fill_opacity=0.7,
                fill_color=color,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{city_name}: {hotel_count} hotels"
            ).add_to(m)
        except Exception as e:
            print(f"Error plotting city {city_name}: {e}")
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: 120px;
                background-color: white; z-index: 9999; padding: 10px;
                border: 2px solid grey; border-radius: 5px; font-size: 12px;">
        <b>Hotel Density Legend</b><br>
        <span style="color: darkblue;">● High Density</span><br>
        <span style="color: blue;">● Medium Density</span><br>
        <span style="color: lightblue;">● Low Density</span><br>
        Max: {max_hotels} hotels
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m


def visualize_optimal_locations(candidates, title="Optimal Hotel Location Candidates"):
    """Visualize optimal hotel location candidates"""
    if not candidates:
        print("Warning: No candidate data to visualize")
        return create_map(11.1271, 78.6569, 7)
    
    m = create_map(11.1271, 78.6569, 7)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 350px; height: 40px; 
                background-color: white; z-index: 9999; padding: 10px;
                border: 2px solid grey; border-radius: 5px;">
        <b>{title}</b>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Find score range for scaling
    valid_candidates = [c for c in candidates if c.get("coordinates") and len(c.get("coordinates", [])) >= 2]
    scores = [c.get("score", 0) for c in valid_candidates]
    max_score = max(scores) if scores else 1
    min_score = min(scores) if scores else -100
    
    score_range = max_score - min_score if max_score > min_score else 1
    
    print(f"Visualizing {len(valid_candidates)} valid candidates (score range: {min_score:.2f} to {max_score:.2f})")
    
    for candidate in valid_candidates:
        coords = candidate.get("coordinates")
        if not coords or len(coords) < 2:
            continue
        
        lat, lon = coords[1], coords[0]
        score = candidate.get("score", 0)
        name = candidate.get("name", "Unknown")
        attraction_density = candidate.get("attraction_density", 0)
        hotel_density = candidate.get("hotel_density", 0)
        city_distance = candidate.get("distance_to_city_km", 0)
        
        # Normalize score for coloring and sizing
        normalized_score = (score - min_score) / score_range if score_range > 0 else 0.5
        
        # Color based on score
        if normalized_score > 0.7:
            color = "darkgreen"
        elif normalized_score > 0.4:
            color = "green"
        else:
            color = "lightgreen"
        
        # Scale radius based on score
        radius = 8 + normalized_score * 15
        
        # Create detailed popup
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px;">
            <h4 style="margin: 0 0 15px 0; color: #333;">{name}</h4>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 6px; border-bottom: 1px solid #eee; font-weight: bold;">Overall Score:</td>
                    <td style="padding: 6px; border-bottom: 1px solid #eee; text-align: right; font-weight: bold; color: {'green' if score > 0 else 'red'};">{score:.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 6px; border-bottom: 1px solid #eee;">Attraction Density:</td>
                    <td style="padding: 6px; border-bottom: 1px solid #eee; text-align: right;">{attraction_density}</td>
                </tr>
                <tr>
                    <td style="padding: 6px; border-bottom: 1px solid #eee;">Hotel Density:</td>
                    <td style="padding: 6px; border-bottom: 1px solid #eee; text-align: right;">{hotel_density}</td>
                </tr>
                <tr>
                    <td style="padding: 6px;">Distance to City:</td>
                    <td style="padding: 6px; text-align: right;">{city_distance:.1f} km</td>
                </tr>
            </table>
            <p style="margin-top: 10px; font-size: 11px; color: #666;">
                <i>Higher scores indicate better locations for new hotels</i>
            </p>
        </div>
        """
        
        try:
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                color=color,
                fill=True,
                fill_opacity=0.8,
                fill_color=color,
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=f"{name}: Score {score:.2f}"
            ).add_to(m)
        except Exception as e:
            print(f"Error plotting candidate {name}: {e}")
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 220px; height: 140px;
                background-color: white; z-index: 9999; padding: 10px;
                border: 2px solid grey; border-radius: 5px; font-size: 12px;">
        <b>Score Legend</b><br>
        <span style="color: darkgreen;">● Excellent (70-100%)</span><br>
        <span style="color: green;">● Good (40-70%)</span><br>
        <span style="color: lightgreen;">● Fair (0-40%)</span><br>
        Score Range: {min_score:.1f} to {max_score:.1f}<br>
        Size = Score Importance
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m


def visualize_district_context(district, cities):
    """Visualize district with cities inside it"""
    if not district:
        print("Warning: No district data for visualization")
        return create_map()
    
    # Try to get centroid
    try:
        from shapely.geometry import shape
        geom = shape(district["geometry"])
        centroid = geom.centroid
        center_lat, center_lon = centroid.y, centroid.x
    except:
        center_lat, center_lon = 13.0827, 80.2707
    
    m = create_map(center_lat=center_lat, center_lon=center_lon, zoom=9)
    
    # Plot district
    plot_geojson(m, district, popup_field="district", color="black", weight=3)
    
    # Plot cities
    if cities:
        plot_points(m, cities, popup_field="name", color="blue", radius=6)
    
    return m


def visualize_any(features, center_lat=13.0827, center_lon=80.2707, zoom=7, title="Map"):
    """Generic visualization function"""
    m = create_map(center_lat, center_lon, zoom)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 300px; height: 40px; 
                background-color: white; z-index: 9999; padding: 10px;
                border: 2px solid grey; border-radius: 5px;">
        <b>{title}</b>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    if isinstance(features, dict):
        plot_geojson(m, features)
    elif isinstance(features, list):
        plot_points(m, features, popup_field="name", color="blue", radius=4)
    else:
        print(f"Warning: Unsupported feature type: {type(features)}")
    
    return m


def save_map_with_debug(map_obj, filename, features_count=None):
    """Save map and print debug info"""
    import os
    
    output_dir = "visualizations"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filepath = os.path.join(output_dir, filename)
    
    try:
        map_obj.save(filepath)
        if features_count is not None:
            print(f"✓ Map saved: {filepath} ({features_count} features plotted)")
        else:
            print(f"✓ Map saved: {filepath}")
        return filepath
    except Exception as e:
        print(f"✗ Error saving map {filename}: {e}")
        return None