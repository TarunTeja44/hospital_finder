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

# Clean, interesting CSS - not childish, not boring
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main {
        padding: 1.5rem 2.5rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Header Section */
    .header-section {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #64748b;
    }
    
    /* Emergency Numbers */
    .emergency-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .emergency-card {
        background: white;
        padding: 1.5rem 1rem;
        border-radius: 12px;
        text-align: center;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .emergency-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    
    .emergency-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .emergency-number {
        font-size: 2rem;
        font-weight: 700;
        color: #dc2626;
        margin: 0.5rem 0;
    }
    
    .emergency-label {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 500;
    }
    
    /* Search Box */
    .search-box {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 2rem 0;
    }
    
    /* Stats Cards */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    .stat-label {
        font-size: 0.95rem;
        color: #64748b;
        margin-top: 0.5rem;
    }
    
    /* Result Cards */
    .result-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        position: relative;
    }
    
    .result-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1rem;
    }
    
    .result-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1e293b;
        margin: 0;
        flex: 1;
    }
    
    .distance-badge {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        white-space: nowrap;
    }
    
    .result-info {
        color: #475569;
        font-size: 0.95rem;
        line-height: 1.8;
        margin: 0.4rem 0;
    }
    
    .result-info strong {
        color: #1e293b;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .result-actions {
        margin-top: 1.2rem;
        display: flex;
        gap: 0.8rem;
    }
    
    .btn-map {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.7rem 1.5rem;
        border-radius: 8px;
        text-decoration: none;
        display: inline-block;
        font-weight: 500;
        transition: all 0.3s ease;
        font-size: 0.95rem;
    }
    
    .btn-map:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
    }
    
    .btn-directions {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 0.7rem 1.5rem;
        border-radius: 8px;
        text-decoration: none;
        display: inline-block;
        font-weight: 500;
        transition: all 0.3s ease;
        font-size: 0.95rem;
    }
    
    .btn-directions:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e293b;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.8rem;
        border-bottom: 3px solid #e2e8f0;
    }
    
    .section-header-small {
        font-size: 1.2rem;
        font-weight: 600;
        color: #334155;
        margin: 1.5rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    
    .count-badge {
        background: #3b82f6;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    /* Show More Button */
    .show-more-container {
        text-align: center;
        margin: 1.5rem 0;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.8rem 2.5rem;
        font-weight: 600;
        font-size: 1.05rem;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
    }
    
    /* Map Container */
    .map-container {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 2rem 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #94a3b8;
        padding: 2rem 0;
        margin-top: 3rem;
        border-top: 2px solid #e2e8f0;
    }
    
    .footer-title {
        font-weight: 600;
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .emergency-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        .stats-container {
            grid-template-columns: 1fr;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="header-section">
        <h1 class="main-title">🏥 Emergency Services Finder</h1>
        <p class="subtitle">Quickly find hospitals, clinics, pharmacies, police stations and emergency services across India</p>
    </div>
""", unsafe_allow_html=True)

# Emergency Numbers
st.markdown("""
    <div class="emergency-grid">
        <div class="emergency-card">
            <div class="emergency-icon">🚔</div>
            <div class="emergency-number">100</div>
            <div class="emergency-label">Police</div>
        </div>
        <div class="emergency-card">
            <div class="emergency-icon">🚒</div>
            <div class="emergency-number">101</div>
            <div class="emergency-label">Fire Brigade</div>
        </div>
        <div class="emergency-card">
            <div class="emergency-icon">🚑</div>
            <div class="emergency-number">108</div>
            <div class="emergency-label">Ambulance</div>
        </div>
        <div class="emergency-card">
            <div class="emergency-icon">👮</div>
            <div class="emergency-number">1091</div>
            <div class="emergency-label">Women Helpline</div>
        </div>
        <div class="emergency-card">
            <div class="emergency-icon">⚠️</div>
            <div class="emergency-number">1078</div>
            <div class="emergency-label">Disaster Mgmt</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Caching Functions
@st.cache_data(ttl=3600)
def geocode_location(place_name):
    try:
        geolocator = Nominatim(user_agent="emergency_services_finder_india_v2")
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
        status_text.text(f"🔍 Searching for {r_type}...")
        
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
                
                # Smart name extraction
                name = tags.get('name') or tags.get('name:en') or tags.get('brand') or tags.get('operator')
                if not name:
                    addr_city = tags.get('addr:city', '')
                    addr_area = tags.get('addr:suburb', tags.get('addr:locality', ''))
                    if addr_city or addr_area:
                        name = f"{r_type} in {addr_area or addr_city}".strip()
                    else:
                        continue
                
                if 'lat' in element and 'lon' in element:
                    rlat, rlon = element['lat'], element['lon']
                elif 'center' in element:
                    rlat, rlon = element['center']['lat'], element['center']['lon']
                else:
                    continue
                
                distance = round(geodesic((lat, lon), (rlat, rlon)).km, 2)
                
                phone = tags.get('phone', tags.get('contact:phone', 'Not available'))
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

# Search Section
st.markdown('<div class="search-box">', unsafe_allow_html=True)
st.markdown("### 🔍 Search for Services")

col1, col2 = st.columns([4, 1])
with col1:
    place_name = st.text_input(
        "Location",
        placeholder="e.g., Connaught Place Delhi, Marine Drive Mumbai, MG Road Bangalore",
        label_visibility="collapsed"
    )
with col2:
    radius_km = st.selectbox(
        "Radius",
        [2, 5, 10, 15, 20, 30],
        index=2,
        format_func=lambda x: f"{x} km",
        label_visibility="collapsed"
    )

st.markdown("#### What are you looking for?")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🏥 Medical**")
    medical = st.multiselect("Medical", ["Hospital", "Clinic", "Pharmacy", "Doctors"], 
                             default=["Hospital", "Pharmacy"], label_visibility="collapsed")

with col2:
    st.markdown("**🚨 Emergency**")
    emergency = st.multiselect("Emergency", ["Police Station", "Fire Station"], 
                               default=["Police Station"], label_visibility="collapsed")

with col3:
    st.markdown("**ℹ️ Other**")
    other = st.multiselect("Other", ["ATM", "Embassy", "Tourist Office"], 
                          default=[], label_visibility="collapsed")

resource_filter = medical + emergency + other

col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    search_button = st.button("🔍 Search Now", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Session state for show more
if 'show_all' not in st.session_state:
    st.session_state.show_all = {}

# Results
if search_button:
    if not place_name.strip():
        st.error("⚠️ Please enter a location")
    elif not resource_filter:
        st.error("⚠️ Please select at least one service")
    else:
        with st.spinner("📍 Finding location..."):
            location = geocode_location(place_name)
        
        if not location:
            st.error("❌ Location not found. Try: 'Area Name, City' (e.g., 'Connaught Place, Delhi')")
        else:
            user_location = (location.latitude, location.longitude)
            st.success(f"✅ {location.address}")
            
            with st.spinner("🔄 Searching for services..."):
                all_results = fetch_resources(location.latitude, location.longitude, radius_km, resource_filter)
            
            if not all_results:
                st.warning("⚠️ No results found. Try increasing radius or selecting more services.")
            else:
                df = pd.DataFrame(all_results)
                df = df.sort_values(by='Distance_km').reset_index(drop=True)
                
                # Stats
                st.markdown("""
                    <div class="stats-container">
                        <div class="stat-card">
                            <div class="stat-number">{}</div>
                            <div class="stat-label">Total Results Found</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{}</div>
                            <div class="stat-label">Service Types</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{} km</div>
                            <div class="stat-label">Nearest Location</div>
                        </div>
                    </div>
                """.format(len(df), len(df['Type'].unique()), df.iloc[0]['Distance_km']), unsafe_allow_html=True)
                
                # Results
                st.markdown('<h2 class="section-header">📋 Search Results</h2>', unsafe_allow_html=True)
                
                for service_type in df['Type'].unique():
                    type_df = df[df['Type'] == service_type]
                    total = len(type_df)
                    
                    st.markdown(f"""
                        <div class="section-header-small">
                            {service_type}
                            <span class="count-badge">{total} found</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Show 5 by default
                    show_count = 5 if not st.session_state.show_all.get(service_type, False) else total
                    display_df = type_df.head(show_count)
                    
                    for idx, row in display_df.iterrows():
                        st.markdown(f"""
                        <div class="result-card">
                            <div class="result-header">
                                <h3 class="result-title">{row['Name']}</h3>
                                <span class="distance-badge">📏 {row['Distance_km']} km</span>
                            </div>
                            <p class="result-info"><strong>📍 Address:</strong>{row['Address']}</p>
                            <p class="result-info"><strong>📞 Phone:</strong>{row['Phone']}</p>
                            <p class="result-info"><strong>🕒 Hours:</strong>{row['Hours']}</p>
                            <div class="result-actions">
                                <a href="{row['Google_Maps']}" target="_blank" class="btn-map">🗺️ View on Map</a>
                                <a href="{row['Directions']}" target="_blank" class="btn-directions">🧭 Get Directions</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Show more button
                    if total > 5:
                        col1, col2, col3 = st.columns([2, 1, 2])
                        with col2:
                            if not st.session_state.show_all.get(service_type, False):
                                if st.button(f"Show All {total}", key=f"show_{service_type}", use_container_width=True):
                                    st.session_state.show_all[service_type] = True
                                    st.rerun()
                            else:
                                if st.button(f"Show Less", key=f"hide_{service_type}", use_container_width=True):
                                    st.session_state.show_all[service_type] = False
                                    st.rerun()
                
                # Map
                st.markdown('<h2 class="section-header">🗺️ Map View</h2>', unsafe_allow_html=True)
                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                
                m = folium.Map(location=user_location, zoom_start=13)
                
                folium.Marker(
                    user_location,
                    popup="<b>📍 Your Location</b>",
                    tooltip="You are here",
                    icon=folium.Icon(color='red', icon='star', prefix='fa')
                ).add_to(m)
                
                colors = {
                    'Hospital': 'blue', 'Clinic': 'lightblue', 'Doctors': 'purple',
                    'Pharmacy': 'green', 'Police Station': 'darkblue', 'Fire Station': 'orange',
                    'ATM': 'gray', 'Embassy': 'pink', 'Tourist Office': 'lightgreen'
                }
                
                for _, row in df.iterrows():
                    popup = f"""
                    <div style="width:260px; font-family: Poppins, sans-serif;">
                        <h3 style="margin:0 0 10px 0;">{row['Name']}</h3>
                        <p style="margin:4px 0;"><b>Type:</b> {row['Type']}</p>
                        <p style="margin:4px 0;"><b>Distance:</b> {row['Distance_km']} km</p>
                        <p style="margin:4px 0;"><b>Phone:</b> {row['Phone']}</p>
                        <div style="margin-top:12px;">
                            <a href="{row['Google_Maps']}" target="_blank" 
                               style="background:#10b981;color:white;padding:8px 14px;text-decoration:none;
                                      border-radius:6px;margin-right:6px;display:inline-block;font-weight:500;">
                                🗺️ View Map
                            </a>
                            <a href="{row['Directions']}" target="_blank" 
                               style="background:#3b82f6;color:white;padding:8px 14px;text-decoration:none;
                                      border-radius:6px;display:inline-block;font-weight:500;">
                                🧭 Directions
                            </a>
                        </div>
                    </div>
                    """
                    folium.Marker(
                        [row['Latitude'], row['Longitude']],
                        popup=folium.Popup(popup, max_width=300),
                        tooltip=f"{row['Name']} ({row['Distance_km']} km)",
                        icon=folium.Icon(color=colors.get(row['Type'], 'gray'), icon='info-sign')
                    ).add_to(m)
                
                folium.Circle(user_location, radius=radius_km*1000, color='#3b82f6', 
                             fill=True, fillOpacity=0.1).add_to(m)
                
                folium_static(m, width=1200, height=600)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Download
                st.markdown('<h2 class="section-header">💾 Download Results</h2>', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button("📥 Download CSV", csv, 
                                     f"services_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                     "text/csv", use_container_width=True)
                with col2:
                    text = f"Emergency Services near {place_name}\n\n"
                    for i, r in df.head(30).iterrows():
                        text += f"{i+1}. {r['Name']} ({r['Type']})\n"
                        text += f"   📏 {r['Distance_km']} km | 📞 {r['Phone']}\n"
                        text += f"   🗺️ {r['Google_Maps']}\n\n"
                    st.download_button("📤 Download Text", text,
                                     f"services_{datetime.now().strftime('%Y%m%d')}.txt",
                                     "text/plain", use_container_width=True)

# Footer
st.markdown("""
    <div class="footer">
        <p class="footer-title">Emergency Services Finder - India</p>
        <p>Powered by OpenStreetMap | For life-threatening emergencies, dial helpline numbers above</p>
        <p style="font-size:0.85rem; margin-top:0.5rem;">🇮🇳 Built for tourists and travelers in India</p>
    </div>
""", unsafe_allow_html=True)
