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
    page_title="Tourist Emergency Services - India",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful interface
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .emergency-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .emergency-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 10px 0;
    }
    .emergency-label {
        font-size: 1.2rem;
        margin-bottom: 5px;
    }
    .result-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #667eea;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 30px;
        font-size: 1.1rem;
        font-weight: bold;
    }
    h1 {
        color: #2d3748;
        text-align: center;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Emergency Numbers Header
st.markdown("<h1>🚑 Tourist Emergency Services Finder - India</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #4a5568;'>Your safety companion while traveling in India</p>", unsafe_allow_html=True)

# Emergency Helpline Numbers at Top
st.markdown("### 🆘 Emergency Helpline Numbers (Available 24/7)")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("""
        <div class="emergency-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
            <div class="emergency-label">🚔 Police</div>
            <div class="emergency-number">100</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="emergency-card" style="background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);">
            <div class="emergency-label">🚒 Fire</div>
            <div class="emergency-number">101</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="emergency-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div class="emergency-label">🚑 Ambulance</div>
            <div class="emergency-number">102</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
        <div class="emergency-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <div class="emergency-label">👮 Women Help</div>
            <div class="emergency-number">1091</div>
        </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
        <div class="emergency-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <div class="emergency-label">🆘 Disaster</div>
            <div class="emergency-number">108</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Caching Functions
@st.cache_data(ttl=3600)
def geocode_location(place_name):
    try:
        geolocator = Nominatim(user_agent="tourist_emergency_finder_india")
        return geolocator.geocode(place_name + ", India", timeout=10)
    except Exception as e:
        return None

@st.cache_data(ttl=1800)
def fetch_resources(lat, lon, radius_km, selected_types):
    """Fetch from both Overpass and use better queries"""
    
    all_resource_queries = {
        "Hospital": '[amenity=hospital]',
        "Clinic": '[amenity=clinic]',
        "Doctors": '[amenity=doctors]',
        "Pharmacy": '[amenity=pharmacy]',
        "Police Station": '[amenity=police]',
        "Fire Station": '[amenity=fire_station]',
        "ATM": '[amenity=atm]',
        "Embassy": '[amenity=embassy]',
        "Tourist Info": '[tourism=information]'
    }
    
    resource_queries = {k: v for k, v in all_resource_queries.items() if k in selected_types}
    
    all_results = []
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, (r_type, tag) in enumerate(resource_queries.items()):
        status_text.text(f"🔍 Searching for {r_type}...")
        
        try:
            # Broader search - fetch nodes, ways AND relations
            query = f"""
            [out:json][timeout:30];
            (
              node(around:{radius_km*1000},{lat},{lon}){tag};
              way(around:{radius_km*1000},{lat},{lon}){tag};
              relation(around:{radius_km*1000},{lat},{lon}){tag};
            );
            out center 200;
            """
            
            res = requests.get(overpass_url, params={'data': query}, timeout=35)
            res.raise_for_status()
            data = res.json()
            
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                name = tags.get('name', tags.get('name:en', tags.get('brand', 'Unnamed')))
                
                # Get coordinates
                if 'lat' in element and 'lon' in element:
                    rlat, rlon = element['lat'], element['lon']
                elif 'center' in element:
                    rlat, rlon = element['center']['lat'], element['center']['lon']
                else:
                    continue
                
                distance = round(geodesic((lat, lon), (rlat, rlon)).km, 2)
                
                # Extract info
                phone = tags.get('phone', tags.get('contact:phone', 'Not Available'))
                website = tags.get('website', tags.get('contact:website', 'Not Available'))
                opening_hours = tags.get('opening_hours', 'Not Available')
                
                # Better address
                addr_parts = []
                for key in ['addr:housenumber', 'addr:street', 'addr:suburb', 
                           'addr:city', 'addr:state']:
                    if tags.get(key):
                        addr_parts.append(tags[key])
                
                address = ', '.join(addr_parts) if addr_parts else tags.get('addr:full', 'Address not available')
                
                # Google Maps links
                google_maps_link = f"https://www.google.com/maps/search/?api=1&query={rlat},{rlon}"
                directions_link = f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={rlat},{rlon}"
                
                all_results.append({
                    'Name': name,
                    'Type': r_type,
                    'Distance_km': distance,
                    'Address': address,
                    'Phone': phone,
                    'Hours': opening_hours,
                    'Website': website,
                    'Latitude': rlat,
                    'Longitude': rlon,
                    'Google_Maps': google_maps_link,
                    'Directions': directions_link
                })
            
            time.sleep(0.5)
            
        except Exception as e:
            st.warning(f"Could not fetch {r_type}: {str(e)[:50]}")
        
        progress_bar.progress((idx + 1) / len(resource_queries))
    
    progress_bar.empty()
    status_text.empty()
    
    return all_results

# Sidebar
with st.sidebar:
    st.markdown("### 🔍 Search Settings")
    
    place_name = st.text_input(
        "📍 Your Location",
        placeholder="e.g., Gateway of India, Mumbai",
        help="Enter your current location or hotel name"
    )
    
    radius_km = st.slider(
        "Search Radius (km)",
        min_value=1,
        max_value=30,
        value=5,
        help="How far to search"
    )
    
    st.markdown("---")
    st.markdown("### 🎯 What do you need?")
    
    # Quick preset buttons
    if st.button("🏥 Medical Emergency", use_container_width=True):
        st.session_state.resource_filter = ["Hospital", "Clinic", "Pharmacy"]
    
    if st.button("🚨 Safety & Security", use_container_width=True):
        st.session_state.resource_filter = ["Police Station", "Fire Station", "Embassy"]
    
    if st.button("💰 Money & Info", use_container_width=True):
        st.session_state.resource_filter = ["ATM", "Tourist Info", "Embassy"]
    
    st.markdown("---")
    
    all_types = ["Hospital", "Clinic", "Doctors", "Pharmacy", 
                 "Police Station", "Fire Station", "ATM", "Embassy", "Tourist Info"]
    
    if 'resource_filter' not in st.session_state:
        st.session_state.resource_filter = ["Hospital", "Police Station", "Pharmacy"]
    
    resource_filter = st.multiselect(
        "Or select specific services:",
        all_types,
        default=st.session_state.resource_filter
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ Tourist Tips")
    st.info("💡 Keep these numbers saved:\n\n🚔 Police: 100\n🚑 Ambulance: 102\n🚒 Fire: 101\n👮 Women Help: 1091")

# Main Search
st.markdown("### 🔎 Find Nearby Services")
search_button = st.button("🔍 Search Now", type="primary", use_container_width=True)

if search_button:
    if not place_name.strip():
        st.error("⚠️ Please enter your location!")
    elif not resource_filter:
        st.error("⚠️ Please select at least one service!")
    else:
        with st.spinner("📍 Locating you..."):
            location = geocode_location(place_name)
        
        if not location:
            st.error("❌ Location not found. Try adding city name (e.g., 'Connaught Place, Delhi')")
        else:
            user_location = (location.latitude, location.longitude)
            
            st.success(f"✅ Found: {location.address}")
            
            with st.spinner(f"🔄 Searching within {radius_km} km..."):
                all_results = fetch_resources(
                    location.latitude,
                    location.longitude,
                    radius_km,
                    resource_filter
                )
            
            if not all_results:
                st.warning("⚠️ No results found nearby. Try:\n- Increasing search radius\n- Selecting more service types\n- Using a different location name")
                st.info("💡 Tip: Some areas may have limited data. Try searching in major city centers.")
            else:
                df = pd.DataFrame(all_results)
                df = df.sort_values(by='Distance_km').reset_index(drop=True)
                
                # Success message
                st.markdown(f"""
                    <div class="info-box">
                        <h3 style='margin:0; color: white;'>✅ Found {len(df)} Services Nearby</h3>
                        <p style='margin:5px 0 0 0; color: white;'>Showing results within {radius_km} km of your location</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # RESULTS FIRST (Before Map)
                st.markdown("### 📋 Results")
                
                # Group by type
                for service_type in df['Type'].unique():
                    type_df = df[df['Type'] == service_type].head(10)  # Show top 10 per type
                    
                    st.markdown(f"#### {service_type} ({len(type_df)} found)")
                    
                    for idx, row in type_df.iterrows():
                        st.markdown(f"""
                        <div class="result-card">
                            <h4 style='margin:0 0 10px 0; color: #2d3748;'>{idx + 1}. {row['Name']}</h4>
                            <p style='margin:5px 0; color: #4a5568;'><strong>📏 Distance:</strong> {row['Distance_km']} km away</p>
                            <p style='margin:5px 0; color: #4a5568;'><strong>📍 Address:</strong> {row['Address']}</p>
                            <p style='margin:5px 0; color: #4a5568;'><strong>📞 Phone:</strong> {row['Phone']}</p>
                            <p style='margin:5px 0; color: #4a5568;'><strong>🕒 Hours:</strong> {row['Hours']}</p>
                            <div style='margin-top: 15px;'>
                                <a href="{row['Google_Maps']}" target="_blank" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; margin-right: 10px; display: inline-block;">🗺️ View on Map</a>
                                <a href="{row['Directions']}" target="_blank" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; display: inline-block;">🧭 Get Directions</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown("---")
                
                # MAP AFTER RESULTS
                st.markdown("### 🗺️ Interactive Map")
                st.markdown("Click on markers to see details and get directions")
                
                m = folium.Map(
                    location=user_location,
                    zoom_start=13,
                    tiles='OpenStreetMap'
                )
                
                # Your location
                folium.Marker(
                    user_location,
                    popup=f"<b>📍 You are here</b><br>{place_name}",
                    tooltip="Your Location",
                    icon=folium.Icon(color='red', icon='star', prefix='fa')
                ).add_to(m)
                
                # Color coding
                color_map = {
                    'Hospital': 'blue', 'Clinic': 'lightblue', 'Doctors': 'purple',
                    'Pharmacy': 'green', 'Police Station': 'darkblue',
                    'Fire Station': 'orange', 'ATM': 'gray',
                    'Embassy': 'pink', 'Tourist Info': 'lightgreen'
                }
                
                for _, row in df.iterrows():
                    popup_html = f"""
                    <div style="width: 280px; font-family: Arial;">
                        <h3 style="margin:0 0 10px 0; color: #2d3748;">{row['Name']}</h3>
                        <p style="margin:3px 0;"><strong>Type:</strong> {row['Type']}</p>
                        <p style="margin:3px 0;"><strong>Distance:</strong> {row['Distance_km']} km</p>
                        <p style="margin:3px 0;"><strong>Phone:</strong> {row['Phone']}</p>
                        <p style="margin:3px 0;"><strong>Address:</strong> {row['Address'][:80]}...</p>
                        <div style="margin-top: 15px;">
                            <a href="{row['Google_Maps']}" target="_blank" 
                               style="background:#4CAF50; color:white; padding:8px 15px; 
                                      text-decoration:none; border-radius:5px; margin-right:5px; 
                                      display:inline-block;">🗺️ View Map</a>
                            <a href="{row['Directions']}" target="_blank" 
                               style="background:#2196F3; color:white; padding:8px 15px; 
                                      text-decoration:none; border-radius:5px; 
                                      display:inline-block;">🧭 Directions</a>
                        </div>
                    </div>
                    """
                    
                    folium.Marker(
                        [row['Latitude'], row['Longitude']],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"{row['Name']} ({row['Distance_km']} km)",
                        icon=folium.Icon(
                            color=color_map.get(row['Type'], 'gray'),
                            icon='info-sign'
                        )
                    ).add_to(m)
                
                # Search radius circle
                folium.Circle(
                    user_location,
                    radius=radius_km * 1000,
                    color='#667eea',
                    fill=True,
                    fillOpacity=0.1,
                    popup=f"Search area: {radius_km} km radius"
                ).add_to(m)
                
                folium_static(m, width=1200, height=600)
                
                st.markdown("---")
                
                # Export options
                st.markdown("### 💾 Save Results")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Complete List (CSV)",
                        data=csv,
                        file_name=f"emergency_services_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    share_text = f"🚑 Emergency Services near {place_name}\n\n"
                    for idx, row in df.head(15).iterrows():
                        share_text += f"{idx+1}. {row['Name']} ({row['Type']})\n"
                        share_text += f"   📏 {row['Distance_km']} km | 📞 {row['Phone']}\n"
                        share_text += f"   🗺️ {row['Google_Maps']}\n\n"
                    
                    st.download_button(
                        label="📤 Share List (Text)",
                        data=share_text,
                        file_name=f"emergency_contacts_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #718096; padding: 20px;'>
    <p><strong>🇮🇳 Tourist Emergency Services Finder for India</strong></p>
    <p>Data from OpenStreetMap | Always verify information before visiting</p>
    <p>💡 <strong>Travel Tip:</strong> Save emergency numbers (100, 101, 102) before traveling</p>
    <p style='font-size: 0.9rem; margin-top: 10px;'>For immediate emergencies, always call the appropriate helpline number</p>
</div>
""", unsafe_allow_html=True)
