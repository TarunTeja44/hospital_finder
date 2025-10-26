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
    layout="wide"
)

# Clean, professional CSS - NO DRAMA
st.markdown("""
    <style>
    .main {
        padding: 1rem 2rem;
    }
    .stApp {
        background-color: #ffffff;
    }
    .emergency-box {
        background-color: #f8f9fa;
        padding: 15px 20px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 8px 5px;
        text-align: center;
    }
    .emergency-number {
        font-size: 1.8rem;
        font-weight: 600;
        color: #dc3545;
        margin: 5px 0;
    }
    .emergency-label {
        font-size: 0.95rem;
        color: #6c757d;
        font-weight: 500;
    }
    .result-item {
        background-color: #ffffff;
        padding: 18px;
        border-radius: 6px;
        margin: 12px 0;
        border: 1px solid #e9ecef;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .result-item:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-color: #dee2e6;
    }
    h1 {
        color: #212529;
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    h2 {
        color: #495057;
        font-size: 1.5rem;
        font-weight: 500;
    }
    h3 {
        color: #495057;
        font-size: 1.25rem;
        font-weight: 500;
    }
    .stButton>button {
        background-color: #0d6efd;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #0b5ed7;
    }
    .info-badge {
        display: inline-block;
        background-color: #e7f3ff;
        color: #084298;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        font-size: 0.9rem;
        margin: 0.2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🏥 Emergency Services Finder")
st.markdown("Find hospitals, clinics, pharmacies, police stations and other essential services near you in India")

# Emergency Numbers - Clean horizontal layout
st.markdown("### 🆘 Emergency Helpline Numbers")
cols = st.columns(5)
emergency_numbers = [
    ("🚔 Police", "100"),
    ("🚒 Fire", "101"),
    ("🚑 Ambulance", "102"),
    ("👮 Women Helpline", "1091"),
    ("🆘 Disaster Mgmt", "108")
]

for col, (label, number) in zip(cols, emergency_numbers):
    with col:
        st.markdown(f"""
            <div class="emergency-box">
                <div class="emergency-label">{label}</div>
                <div class="emergency-number">{number}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Caching
@st.cache_data(ttl=3600)
def geocode_location(place_name):
    try:
        geolocator = Nominatim(user_agent="emergency_services_finder_india")
        return geolocator.geocode(place_name + ", India", timeout=10)
    except:
        return None

@st.cache_data(ttl=1800)
def fetch_resources(lat, lon, radius_km, selected_types):
    all_resource_queries = {
        "Hospital": '[amenity=hospital]',
        "Clinic": '[amenity=clinic]',
        "Pharmacy": '[amenity=pharmacy]',
        "Doctors": '[amenity=doctors]',
        "Police Station": '[amenity=police]',
        "Fire Station": '[amenity=fire_station]',
        "ATM": '[amenity=atm]',
        "Embassy": '[amenity=embassy]',
        "Tourist Office": '[tourism=information]'
    }
    
    resource_queries = {k: v for k, v in all_resource_queries.items() if k in selected_types}
    all_results = []
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, (r_type, tag) in enumerate(resource_queries.items()):
        status_text.text(f"Searching for {r_type}...")
        
        try:
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
                
                if 'lat' in element and 'lon' in element:
                    rlat, rlon = element['lat'], element['lon']
                elif 'center' in element:
                    rlat, rlon = element['center']['lat'], element['center']['lon']
                else:
                    continue
                
                distance = round(geodesic((lat, lon), (rlat, rlon)).km, 2)
                
                phone = tags.get('phone', tags.get('contact:phone', 'Not available'))
                website = tags.get('website', tags.get('contact:website', 'Not available'))
                opening_hours = tags.get('opening_hours', 'Not available')
                
                addr_parts = []
                for key in ['addr:housenumber', 'addr:street', 'addr:suburb', 'addr:city', 'addr:state']:
                    if tags.get(key):
                        addr_parts.append(tags[key])
                
                address = ', '.join(addr_parts) if addr_parts else tags.get('addr:full', 'Address not available')
                
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
        except:
            pass
        
        progress_bar.progress((idx + 1) / len(resource_queries))
    
    progress_bar.empty()
    status_text.empty()
    return all_results

# Search Section - LEFT SIDE (main area)
st.markdown("## Search for Services")

col1, col2, col3 = st.columns([3, 2, 2])

with col1:
    place_name = st.text_input(
        "📍 Enter your location",
        placeholder="e.g., Connaught Place Delhi, Gateway of India Mumbai",
        label_visibility="collapsed"
    )

with col2:
    radius_km = st.selectbox(
        "Search radius",
        [2, 5, 10, 15, 20, 30],
        index=2,
        label_visibility="collapsed"
    )
    st.markdown(f"<small>Within {radius_km} km</small>", unsafe_allow_html=True)

with col3:
    pass  # Empty for spacing

# Service type selection - BELOW search, not in sidebar
st.markdown("#### Select services you need:")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Medical Services**")
    medical = st.multiselect(
        "Medical",
        ["Hospital", "Clinic", "Pharmacy", "Doctors"],
        default=["Hospital", "Pharmacy"],
        label_visibility="collapsed"
    )

with col2:
    st.markdown("**Emergency Services**")
    emergency = st.multiselect(
        "Emergency",
        ["Police Station", "Fire Station"],
        default=["Police Station"],
        label_visibility="collapsed"
    )

with col3:
    st.markdown("**Other Services**")
    other = st.multiselect(
        "Other",
        ["ATM", "Embassy", "Tourist Office"],
        default=[],
        label_visibility="collapsed"
    )

resource_filter = medical + emergency + other

st.markdown("<br>", unsafe_allow_html=True)

# Search button
search_col1, search_col2, search_col3 = st.columns([2, 1, 2])
with search_col2:
    search_button = st.button("🔍 Search", type="primary", use_container_width=True)

st.markdown("---")

# Results
if search_button:
    if not place_name.strip():
        st.error("Please enter a location")
    elif not resource_filter:
        st.error("Please select at least one service type")
    else:
        with st.spinner("Finding location..."):
            location = geocode_location(place_name)
        
        if not location:
            st.error("Location not found. Try adding city name (e.g., 'Connaught Place, Delhi')")
        else:
            user_location = (location.latitude, location.longitude)
            st.success(f"📍 {location.address}")
            
            with st.spinner("Searching for services..."):
                all_results = fetch_resources(location.latitude, location.longitude, radius_km, resource_filter)
            
            if not all_results:
                st.warning("No results found. Try increasing the search radius or selecting more service types.")
            else:
                df = pd.DataFrame(all_results)
                df = df.sort_values(by='Distance_km').reset_index(drop=True)
                
                st.success(f"✅ Found {len(df)} services")
                
                # Results section
                st.markdown("## Search Results")
                
                for service_type in df['Type'].unique():
                    type_df = df[df['Type'] == service_type].head(10)
                    
                    st.markdown(f"### {service_type}")
                    st.markdown(f"<small>{len(type_df)} locations found</small>", unsafe_allow_html=True)
                    
                    for idx, row in type_df.iterrows():
                        with st.container():
                            st.markdown(f"""
                            <div class="result-item">
                                <h4 style='margin: 0 0 8px 0; color: #212529;'>{row['Name']}</h4>
                                <p style='margin: 4px 0; color: #6c757d;'><strong>Distance:</strong> {row['Distance_km']} km</p>
                                <p style='margin: 4px 0; color: #6c757d;'><strong>Address:</strong> {row['Address']}</p>
                                <p style='margin: 4px 0; color: #6c757d;'><strong>Phone:</strong> {row['Phone']}</p>
                                <p style='margin: 4px 0; color: #6c757d;'><strong>Hours:</strong> {row['Hours']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])
                            with btn_col1:
                                st.markdown(f"[🗺️ View Map]({row['Google_Maps']})")
                            with btn_col2:
                                st.markdown(f"[🧭 Directions]({row['Directions']})")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Map section
                st.markdown("## Map View")
                
                m = folium.Map(location=user_location, zoom_start=13, tiles='OpenStreetMap')
                
                folium.Marker(
                    user_location,
                    popup="Your Location",
                    tooltip="You are here",
                    icon=folium.Icon(color='red', icon='star', prefix='fa')
                ).add_to(m)
                
                color_map = {
                    'Hospital': 'blue', 'Clinic': 'lightblue', 'Doctors': 'purple',
                    'Pharmacy': 'green', 'Police Station': 'darkblue',
                    'Fire Station': 'orange', 'ATM': 'gray',
                    'Embassy': 'pink', 'Tourist Office': 'lightgreen'
                }
                
                for _, row in df.iterrows():
                    popup_html = f"""
                    <div style="width: 250px;">
                        <h4 style="margin: 0 0 8px 0;">{row['Name']}</h4>
                        <p style="margin: 3px 0;"><strong>Type:</strong> {row['Type']}</p>
                        <p style="margin: 3px 0;"><strong>Distance:</strong> {row['Distance_km']} km</p>
                        <p style="margin: 3px 0;"><strong>Phone:</strong> {row['Phone']}</p>
                        <br>
                        <a href="{row['Google_Maps']}" target="_blank" style="background:#28a745; color:white; padding:6px 12px; text-decoration:none; border-radius:4px; margin-right:5px;">View Map</a>
                        <a href="{row['Directions']}" target="_blank" style="background:#007bff; color:white; padding:6px 12px; text-decoration:none; border-radius:4px;">Directions</a>
                    </div>
                    """
                    
                    folium.Marker(
                        [row['Latitude'], row['Longitude']],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"{row['Name']} ({row['Distance_km']} km)",
                        icon=folium.Icon(color=color_map.get(row['Type'], 'gray'), icon='info-sign')
                    ).add_to(m)
                
                folium.Circle(
                    user_location,
                    radius=radius_km * 1000,
                    color='blue',
                    fill=True,
                    fillOpacity=0.1
                ).add_to(m)
                
                folium_static(m, width=1200, height=600)
                
                st.markdown("---")
                
                # Download section
                st.markdown("## Download Results")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        f"services_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    share_text = f"Emergency Services near {place_name}\n\n"
                    for idx, row in df.head(20).iterrows():
                        share_text += f"{idx+1}. {row['Name']} ({row['Type']})\n"
                        share_text += f"   {row['Distance_km']} km | {row['Phone']}\n"
                        share_text += f"   {row['Google_Maps']}\n\n"
                    
                    st.download_button(
                        "📤 Download Text",
                        share_text,
                        f"services_{datetime.now().strftime('%Y%m%d')}.txt",
                        "text/plain",
                        use_container_width=True
                    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d; padding: 20px; font-size: 0.9rem;'>
    <p><strong>Emergency Services Finder - India</strong></p>
    <p>Data from OpenStreetMap | For emergencies, always call the helpline numbers above</p>
</div>
""", unsafe_allow_html=True)
