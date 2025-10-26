import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
from datetime import datetime
import folium
from streamlit_folium import folium_static
import time

st.set_page_config(
    page_title="Emergency Services Finder - India",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {padding: 1rem;}
    .stAlert {border-radius: 0.5rem;}
    h1 {color: #1f77b4;}
    </style>
""", unsafe_allow_html=True)

st.title("🏥 Emergency Services & Healthcare Finder - India")
st.markdown("Find nearby hospitals, clinics, police stations, and emergency services")

# --- Caching Functions ---
@st.cache_data(ttl=3600)
def geocode_location(place_name):
    """Cache geocoding for 1 hour"""
    try:
        geolocator = Nominatim(user_agent="healthcare_finder_india_v3")
        return geolocator.geocode(place_name + ", India", timeout=10)
    except Exception as e:
        st.error(f"Geocoding error: {e}")
        return None

@st.cache_data(ttl=1800)
def fetch_resources(lat, lon, radius_km, selected_types):
    """Cache resource queries for 30 minutes"""
    
    all_resource_queries = {
        "Hospital": '[amenity=hospital]',
        "Clinic": '[amenity=clinic]',
        "Doctors": '[amenity=doctors]',
        "Health Centre": '[healthcare=centre]',
        "Police Station": '[amenity=police]',
        "Fire Station": '[amenity=fire_station]',
        "Pharmacy": '[amenity=pharmacy]',
        "Blood Bank": '[healthcare=blood_donation]',
        "Ambulance Station": '[emergency=ambulance_station]'
    }
    
    # Filter based on user selection
    resource_queries = {k: v for k, v in all_resource_queries.items() 
                       if k in selected_types}
    
    all_results = []
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, (r_type, tag) in enumerate(resource_queries.items()):
        status_text.text(f"🔍 Searching for {r_type}...")
        
        try:
            # Enhanced query: fetch both nodes and ways
            query = f"""
            [out:json][timeout:30];
            (
              node(around:{radius_km*1000},{lat},{lon}){tag};
              way(around:{radius_km*1000},{lat},{lon}){tag};
            );
            out center 150;
            """
            
            res = requests.get(overpass_url, params={'data': query}, timeout=35)
            res.raise_for_status()
            data = res.json()
            
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                name = tags.get('name', tags.get('name:en', 'Unnamed'))
                
                # Get coordinates (handle both nodes and ways)
                if 'lat' in element and 'lon' in element:
                    rlat, rlon = element['lat'], element['lon']
                elif 'center' in element:
                    rlat, rlon = element['center']['lat'], element['center']['lon']
                else:
                    continue
                
                distance = round(geodesic((lat, lon), (rlat, rlon)).km, 2)
                
                # Enhanced data extraction
                phone = tags.get('phone', tags.get('contact:phone', 'N/A'))
                website = tags.get('website', tags.get('contact:website', 'N/A'))
                opening_hours = tags.get('opening_hours', 'N/A')
                emergency_service = tags.get('emergency', 'N/A')
                beds = tags.get('beds', 'N/A')
                operator = tags.get('operator', tags.get('operator:type', 'N/A'))
                
                # Enhanced address extraction
                addr_parts = []
                for key in ['addr:housenumber', 'addr:street', 'addr:suburb', 
                           'addr:city', 'addr:district', 'addr:state', 'addr:postcode']:
                    if tags.get(key):
                        addr_parts.append(tags[key])
                
                if not addr_parts and tags.get('addr:full'):
                    address = tags['addr:full']
                elif addr_parts:
                    address = ', '.join(addr_parts)
                else:
                    address = f"Lat: {rlat:.4f}, Lon: {rlon:.4f}"
                
                # Create Google Maps links
                google_maps_link = f"https://www.google.com/maps/search/?api=1&query={rlat},{rlon}"
                directions_link = f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={rlat},{rlon}"
                
                all_results.append({
                    'Name': name,
                    'Type': r_type,
                    'Distance_km': distance,
                    'Address': address,
                    'Phone': phone,
                    'Opening_Hours': opening_hours,
                    'Emergency': emergency_service,
                    'Beds': beds,
                    'Operator': operator,
                    'Website': website,
                    'Latitude': rlat,
                    'Longitude': rlon,
                    'Google_Maps': google_maps_link,
                    'Directions': directions_link
                })
            
            # Rate limiting: small delay between requests
            time.sleep(0.5)
            
        except requests.Timeout:
            st.warning(f"⏰ Timeout fetching {r_type}. Try reducing search radius.")
        except requests.RequestException as e:
            st.warning(f"🌐 Network error for {r_type}: {str(e)[:50]}")
        except Exception as e:
            st.warning(f"⚠️ Error fetching {r_type}: {str(e)[:50]}")
        
        # Update progress
        progress_bar.progress((idx + 1) / len(resource_queries))
    
    progress_bar.empty()
    status_text.empty()
    
    return all_results

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Search Configuration")
    
    place_name = st.text_input(
        "📍 Enter Location",
        placeholder="e.g., Connaught Place, Delhi",
        help="Enter a city, area, or specific location in India"
    )
    
    radius_km = st.slider(
        "🔍 Search Radius (km)",
        min_value=1,
        max_value=50,
        value=10,
        help="Larger radius = more results but slower search"
    )
    
    st.divider()
    
    st.header("🔧 Resource Filters")
    
    all_types = [
        "Hospital", "Clinic", "Doctors", "Health Centre",
        "Police Station", "Fire Station", "Pharmacy", 
        "Blood Bank", "Ambulance Station"
    ]
    
    # Quick select buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Healthcare", use_container_width=True):
            st.session_state.resource_filter = [
                "Hospital", "Clinic", "Doctors", "Health Centre", "Pharmacy"
            ]
    with col2:
        if st.button("Emergency", use_container_width=True):
            st.session_state.resource_filter = [
                "Hospital", "Police Station", "Fire Station", "Ambulance Station"
            ]
    
    if 'resource_filter' not in st.session_state:
        st.session_state.resource_filter = ["Hospital", "Clinic", "Police Station"]
    
    resource_filter = st.multiselect(
        "Select Resource Types",
        all_types,
        default=st.session_state.resource_filter,
        help="Select one or more resource types to find"
    )
    
    st.divider()
    
    st.header("📊 Display Options")
    show_map = st.checkbox("Show Map", value=True)
    show_contact = st.checkbox("Show Contact Details", value=True)
    show_stats = st.checkbox("Show Statistics", value=True)
    sort_by = st.selectbox(
        "Sort Results By",
        ["Distance", "Name", "Type"],
        index=0
    )
    
    max_results = st.selectbox(
        "Results per page",
        [10, 25, 50, 100, "All"],
        index=2
    )

# --- Main Content ---
search_button = st.button("🔎 Find Nearby Resources", type="primary", use_container_width=True)

if search_button:
    if not place_name.strip():
        st.error("⚠️ Please enter a location!")
    elif not resource_filter:
        st.error("⚠️ Please select at least one resource type!")
    else:
        with st.spinner("📍 Finding location..."):
            location = geocode_location(place_name)
        
        if not location:
            st.error("❌ Location not found. Please try a more specific location or include the city name.")
        else:
            user_location = (location.latitude, location.longitude)
            
            st.success(f"✅ Location: {location.address}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📍 Latitude: {location.latitude:.6f}")
            with col2:
                st.info(f"📍 Longitude: {location.longitude:.6f}")
            
            with st.spinner(f"🔄 Searching within {radius_km} km..."):
                all_results = fetch_resources(
                    location.latitude,
                    location.longitude,
                    radius_km,
                    resource_filter
                )
            
            if not all_results:
                st.warning("ℹ️ No resources found. Try increasing the search radius or selecting more resource types.")
            else:
                df = pd.DataFrame(all_results)
                
                if sort_by == "Distance":
                    df = df.sort_values(by='Distance_km')
                elif sort_by == "Name":
                    df = df.sort_values(by='Name')
                else:
                    df = df.sort_values(by='Type')
                
                df = df.reset_index(drop=True)
                
                st.success(f"✅ Found **{len(df)}** resources within {radius_km} km")
                
                if show_stats:
                    st.subheader("📊 Resource Statistics")
                    
                    type_counts = df['Type'].value_counts()
                    
                    cols = st.columns(min(len(type_counts), 5))
                    for idx, (rtype, count) in enumerate(type_counts.items()):
                        with cols[idx % 5]:
                            avg_dist = df[df['Type'] == rtype]['Distance_km'].mean()
                            st.metric(
                                label=rtype,
                                value=count,
                                delta=f"Avg: {avg_dist:.1f} km"
                            )
                    
                    st.divider()
                
                if show_map:
                    st.subheader("🗺️ Interactive Map (Click markers for details)")
                    
                    m = folium.Map(
                        location=user_location,
                        zoom_start=12,
                        tiles='OpenStreetMap'
                    )
                    
                    folium.Marker(
                        user_location,
                        popup=f"<b>Your Location</b><br>{place_name}",
                        tooltip="You are here",
                        icon=folium.Icon(color='red', icon='home', prefix='fa')
                    ).add_to(m)
                    
                    color_map = {
                        'Hospital': 'blue',
                        'Clinic': 'lightblue',
                        'Doctors': 'purple',
                        'Health Centre': 'cadetblue',
                        'Police Station': 'darkblue',
                        'Fire Station': 'orange',
                        'Pharmacy': 'green',
                        'Blood Bank': 'red',
                        'Ambulance Station': 'lightred'
                    }
                    
                    for _, row in df.iterrows():
                        popup_html = f"""
                        <div style="width: 250px;">
                            <h4>{row['Name']}</h4>
                            <b>Type:</b> {row['Type']}<br>
                            <b>Distance:</b> {row['Distance_km']} km<br>
                            <b>Address:</b> {row['Address'][:60]}...<br>
                        """
                        
                        if row['Phone'] != 'N/A':
                            popup_html += f"<b>Phone:</b> {row['Phone']}<br>"
                        
                        if row['Opening_Hours'] != 'N/A':
                            popup_html += f"<b>Hours:</b> {row['Opening_Hours']}<br>"
                        
                        popup_html += f"""
                            <br>
                            <a href="{row['Google_Maps']}" target="_blank" style="background-color:#4CAF50;color:white;padding:5px 10px;text-decoration:none;border-radius:4px;margin-right:5px;">View on Map</a>
                            <a href="{row['Directions']}" target="_blank" style="background-color:#2196F3;color:white;padding:5px 10px;text-decoration:none;border-radius:4px;">Get Directions</a>
                        </div>
                        """
                        
                        folium.Marker(
                            [row['Latitude'], row['Longitude']],
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=row['Name'],
                            icon=folium.Icon(
                                color=color_map.get(row['Type'], 'gray'),
                                icon='info-sign'
                            )
                        ).add_to(m)
                    
                    folium.Circle(
                        user_location,
                        radius=radius_km * 1000,
                        color='red',
                        fill=True,
                        opacity=0.1
                    ).add_to(m)
                    
                    folium_static(m, width=1200, height=500)
                    
                    st.divider()
                
                st.subheader("📋 Detailed Results")
                
                display_df = df.copy()
                if max_results != "All":
                    display_df = display_df.head(max_results)
                
                for idx, row in display_df.iterrows():
                    with st.expander(f"**{idx + 1}. {row['Name']}** - {row['Type']} ({row['Distance_km']} km)", expanded=(idx < 3)):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**📍 Address:** {row['Address']}")
                            if row['Phone'] != 'N/A':
                                st.write(f"**📞 Phone:** {row['Phone']}")
                            if row['Opening_Hours'] != 'N/A':
                                st.write(f"**🕐 Hours:** {row['Opening_Hours']}")
                        
                        with col2:
                            st.write(f"**📏 Distance:** {row['Distance_km']} km")
                            if row['Operator'] != 'N/A':
                                st.write(f"**🏢 Operator:** {row['Operator']}")
                            if row['Beds'] != 'N/A':
                                st.write(f"**🛏️ Beds:** {row['Beds']}")
                        
                        with col3:
                            st.markdown(f"[🗺️ View Map]({row['Google_Maps']})", unsafe_allow_html=True)
                            st.markdown(f"[🧭 Directions]({row['Directions']})", unsafe_allow_html=True)
                            if row['Website'] != 'N/A':
                                st.markdown(f"[🌐 Website]({row['Website']})", unsafe_allow_html=True)
                
                if len(df) > max_results and max_results != "All":
                    st.info(f"Showing {max_results} of {len(df)} results. Change 'Results per page' in sidebar to see more.")
                
                st.divider()
                
                st.subheader("💾 Export Data")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Full Data (CSV)",
                        data=csv,
                        file_name=f"healthcare_finder_{place_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    summary_df = df[['Name', 'Type', 'Distance_km', 'Phone', 'Google_Maps', 'Directions']].copy()
                    summary_csv = summary_df.to_csv(index=False)
                    st.download_button(
                        label="📄 Download with Links (CSV)",
                        data=summary_csv,
                        file_name=f"summary_with_links_{place_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col3:
                    share_text = f"Nearby Resources near {place_name}:\n\n"
                    for idx, row in df.head(10).iterrows():
                        share_text += f"{idx+1}. {row['Name']} ({row['Type']})\n"
                        share_text += f"   Distance: {row['Distance_km']} km\n"
                        share_text += f"   Map: {row['Google_Maps']}\n\n"
                    
                    st.download_button(
                        label="📤 Share as Text",
                        data=share_text,
                        file_name=f"share_{place_name.replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                st.divider()
                
                available_types = set(df['Type'].unique())
                missing_types = set(resource_filter) - available_types
                
                if missing_types:
                    st.info(f"ℹ️ No results found for: {', '.join(missing_types)}")

st.divider()
st.caption("Data source: OpenStreetMap | Built with Streamlit | Geocoding: Nominatim")
st.caption("⚠️ Note: Results depend on OSM data completeness. Some facilities may be missing.")
st.caption("💡 Tip: Click on map markers or use the buttons to open locations in Google Maps")
