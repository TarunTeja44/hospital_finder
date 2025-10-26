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
    page_title="Emergency Services - India",
    page_icon="🏥",
    layout="wide"
)

# Compact, clean CSS - everything properly sized
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        padding: 1rem 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .stApp {
        background-color: #ffffff;
    }
    
    /* Compact Header */
    .header {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1.5rem;
    }
    
    .header h1 {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1f2937;
        margin: 0 0 0.3rem 0;
    }
    
    .header p {
        font-size: 0.9rem;
        color: #6b7280;
        margin: 0;
    }
    
    /* Compact Emergency Numbers */
    .emergency-row {
        display: flex;
        gap: 0.5rem;
        margin: 1rem 0;
        justify-content: center;
    }
    
    .emergency-item {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        text-align: center;
        min-width: 100px;
    }
    
    .emergency-item:hover {
        background: #f3f4f6;
        border-color: #3b82f6;
    }
    
    .em-label {
        font-size: 0.75rem;
        color: #6b7280;
        margin-bottom: 0.2rem;
    }
    
    .em-number {
        font-size: 1.3rem;
        font-weight: 700;
        color: #dc2626;
    }
    
    /* Compact Search Box */
    .search-container {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1.2rem;
        margin: 1rem 0;
    }
    
    /* Compact Result Card */
    .result-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.6rem 0;
        transition: all 0.2s;
    }
    
    .result-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.6rem;
    }
    
    .result-name {
        font-size: 1rem;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
    }
    
    .result-distance {
        background: #3b82f6;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .result-info {
        font-size: 0.85rem;
        color: #4b5563;
        margin: 0.3rem 0;
        line-height: 1.4;
    }
    
    .result-info strong {
        color: #1f2937;
        font-weight: 500;
    }
    
    .result-buttons {
        margin-top: 0.7rem;
        display: flex;
        gap: 0.5rem;
    }
    
    .btn {
        padding: 0.4rem 1rem;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.85rem;
        font-weight: 500;
        display: inline-block;
        transition: all 0.2s;
    }
    
    .btn-map {
        background: #10b981;
        color: white;
    }
    
    .btn-map:hover {
        background: #059669;
    }
    
    .btn-dir {
        background: #3b82f6;
        color: white;
    }
    
    .btn-dir:hover {
        background: #2563eb;
    }
    
    /* Section Headers - Compact */
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f2937;
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }
    
    .type-header {
        font-size: 0.95rem;
        font-weight: 600;
        color: #374151;
        margin: 1rem 0 0.5rem 0;
    }
    
    .count-badge {
        background: #3b82f6;
        color: white;
        padding: 0.15rem 0.5rem;
        border-radius: 10px;
        font-size: 0.75rem;
        margin-left: 0.5rem;
    }
    
    /* Stats - Compact */
    .stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.8rem;
        margin: 1rem 0;
    }
    
    .stat-box {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.8rem;
        text-align: center;
    }
    
    .stat-num {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f2937;
    }
    
    .stat-label {
        font-size: 0.75rem;
        color: #6b7280;
        margin-top: 0.2rem;
    }
    
    /* Buttons */
    .stButton>button {
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    .stButton>button:hover {
        background: #2563eb;
    }
    
    /* Reduce input sizes */
    .stTextInput>div>div>input {
        font-size: 0.9rem;
        padding: 0.5rem;
    }
    
    .stSelectbox>div>div>div {
        font-size: 0.9rem;
    }
    
    .stMultiSelect>div>div>div {
        font-size: 0.85rem;
    }
    
    /* Footer - Compact */
    .footer {
        text-align: center;
        font-size: 0.8rem;
        color: #9ca3af;
        padding: 1.5rem 0;
        margin-top: 2rem;
        border-top: 1px solid #e5e7eb;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .emergency-row {
            flex-wrap: wrap;
        }
        .stats {
            grid-template-columns: 1fr;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Header - Compact
st.markdown("""
    <div class="header">
        <h1>🏥 Emergency Services Finder</h1>
        <p>Find nearby hospitals, clinics, pharmacies, police and emergency services in India</p>
    </div>
""", unsafe_allow_html=True)

# Emergency Numbers - Compact
st.markdown("""
    <div class="emergency-row">
        <div class="emergency-item">
            <div class="em-label">🚔 Police</div>
            <div class="em-number">100</div>
        </div>
        <div class="emergency-item">
            <div class="em-label">🚒 Fire</div>
            <div class="em-number">101</div>
        </div>
        <div class="emergency-item">
            <div class="em-label">🚑 Ambulance</div>
            <div class="em-number">108</div>
        </div>
        <div class="emergency-item">
            <div class="em-label">👮 Women</div>
            <div class="em-number">1091</div>
        </div>
        <div class="emergency-item">
            <div class="em-label">⚠️ Disaster</div>
            <div class="em-number">1078</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Functions
@st.cache_data(ttl=3600)
def geocode_location(place_name):
    try:
        geolocator = Nominatim(user_agent="emergency_finder_india")
        return geolocator.geocode(place_name + ", India", timeout=10)
    except:
        return None

@st.cache_data(ttl=1800)
def fetch_resources(lat, lon, radius_km, selected_types):
    queries = {
        "Hospital": '[amenity=hospital]', "Clinic": '[amenity=clinic]',
        "Pharmacy": '[amenity=pharmacy]', "Doctors": '[amenity=doctors]',
        "Police Station": '[amenity=police]', "Fire Station": '[amenity=fire_station]',
        "ATM": '[amenity=atm]', "Embassy": '[amenity=embassy]',
        "Tourist Office": '[tourism=information]'
    }
    
    queries = {k: v for k, v in queries.items() if k in selected_types}
    results = []
    url = "https://overpass-api.de/api/interpreter"
    
    progress = st.progress(0)
    status = st.empty()
    
    for idx, (r_type, tag) in enumerate(queries.items()):
        status.text(f"Searching {r_type}...")
        
        try:
            q = f"""
            [out:json][timeout:30];
            (
              node(around:{radius_km*1000},{lat},{lon}){tag};
              way(around:{radius_km*1000},{lat},{lon}){tag};
              relation(around:{radius_km*1000},{lat},{lon}){tag};
            );
            out center 200;
            """
            
            res = requests.get(url, params={'data': q}, timeout=35)
            res.raise_for_status()
            data = res.json()
            
            for elem in data.get('elements', []):
                tags = elem.get('tags', {})
                
                name = tags.get('name') or tags.get('name:en') or tags.get('brand') or tags.get('operator')
                if not name:
                    city = tags.get('addr:city', '')
                    area = tags.get('addr:suburb', tags.get('addr:locality', ''))
                    if city or area:
                        name = f"{r_type} in {area or city}".strip()
                    else:
                        continue
                
                if 'lat' in elem and 'lon' in elem:
                    rlat, rlon = elem['lat'], elem['lon']
                elif 'center' in elem:
                    rlat, rlon = elem['center']['lat'], elem['center']['lon']
                else:
                    continue
                
                dist = round(geodesic((lat, lon), (rlat, rlon)).km, 2)
                phone = tags.get('phone', tags.get('contact:phone', 'N/A'))
                hours = tags.get('opening_hours', 'N/A')
                
                addr_parts = [tags.get(k, '') for k in ['addr:housenumber', 'addr:street', 'addr:suburb', 'addr:city', 'addr:state'] if tags.get(k)]
                address = ', '.join(addr_parts) if addr_parts else tags.get('addr:full', 'N/A')
                
                maps = f"https://www.google.com/maps/search/?api=1&query={rlat},{rlon}"
                dirs = f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={rlat},{rlon}"
                
                results.append({
                    'Name': name, 'Type': r_type, 'Distance_km': dist,
                    'Address': address, 'Phone': phone, 'Hours': hours,
                    'Latitude': rlat, 'Longitude': rlon,
                    'Google_Maps': maps, 'Directions': dirs
                })
            
            time.sleep(0.5)
        except:
            pass
        
        progress.progress((idx + 1) / len(queries))
    
    progress.empty()
    status.empty()
    return results

# Search - Compact
st.markdown('<div class="search-container">', unsafe_allow_html=True)

col1, col2 = st.columns([4, 1])
with col1:
    place_name = st.text_input("Location", placeholder="e.g., Connaught Place Delhi", label_visibility="collapsed")
with col2:
    radius_km = st.selectbox("Radius", [2, 5, 10, 15, 20, 30], index=2, format_func=lambda x: f"{x} km", label_visibility="collapsed")

col1, col2, col3 = st.columns(3)
with col1:
    medical = st.multiselect("🏥 Medical", ["Hospital", "Clinic", "Pharmacy", "Doctors"], default=["Hospital"], label_visibility="collapsed")
with col2:
    emergency = st.multiselect("🚨 Emergency", ["Police Station", "Fire Station"], default=["Police Station"], label_visibility="collapsed")
with col3:
    other = st.multiselect("ℹ️ Other", ["ATM", "Embassy", "Tourist Office"], default=[], label_visibility="collapsed")

resource_filter = medical + emergency + other

col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    search_btn = st.button("Search", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Session state
if 'show_all' not in st.session_state:
    st.session_state.show_all = {}

# Results
if search_btn:
    if not place_name.strip():
        st.error("Enter a location")
    elif not resource_filter:
        st.error("Select at least one service")
    else:
        with st.spinner("Finding location..."):
            location = geocode_location(place_name)
        
        if not location:
            st.error("Location not found. Try: 'Area, City'")
        else:
            user_loc = (location.latitude, location.longitude)
            st.success(f"✓ {location.address}")
            
            with st.spinner("Searching..."):
                all_results = fetch_resources(location.latitude, location.longitude, radius_km, resource_filter)
            
            if not all_results:
                st.warning("No results found. Try increasing radius.")
            else:
                df = pd.DataFrame(all_results)
                df = df.sort_values(by='Distance_km').reset_index(drop=True)
                
                # Stats - Compact
                st.markdown(f"""
                    <div class="stats">
                        <div class="stat-box">
                            <div class="stat-num">{len(df)}</div>
                            <div class="stat-label">Results</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-num">{len(df['Type'].unique())}</div>
                            <div class="stat-label">Types</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-num">{df.iloc[0]['Distance_km']} km</div>
                            <div class="stat-label">Nearest</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Results - Compact
                st.markdown('<div class="section-title">Results</div>', unsafe_allow_html=True)
                
                for stype in df['Type'].unique():
                    type_df = df[df['Type'] == stype]
                    total = len(type_df)
                    
                    st.markdown(f'<div class="type-header">{stype} <span class="count-badge">{total}</span></div>', unsafe_allow_html=True)
                    
                    show = 3 if not st.session_state.show_all.get(stype, False) else total
                    display_df = type_df.head(show)
                    
                    for idx, row in display_df.iterrows():
                        st.markdown(f"""
                        <div class="result-card">
                            <div class="result-header">
                                <div class="result-name">{row['Name']}</div>
                                <div class="result-distance">{row['Distance_km']} km</div>
                            </div>
                            <div class="result-info"><strong>📍</strong> {row['Address']}</div>
                            <div class="result-info"><strong>📞</strong> {row['Phone']}</div>
                            <div class="result-info"><strong>🕒</strong> {row['Hours']}</div>
                            <div class="result-buttons">
                                <a href="{row['Google_Maps']}" target="_blank" class="btn btn-map">View Map</a>
                                <a href="{row['Directions']}" target="_blank" class="btn btn-dir">Directions</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if total > 3:
                        if not st.session_state.show_all.get(stype, False):
                            if st.button(f"Show all {total}", key=f"s_{stype}"):
                                st.session_state.show_all[stype] = True
                                st.rerun()
                        else:
                            if st.button(f"Show less", key=f"h_{stype}"):
                                st.session_state.show_all[stype] = False
                                st.rerun()
                
                # Map - Compact
                st.markdown('<div class="section-title">Map</div>', unsafe_allow_html=True)
                
                m = folium.Map(location=user_loc, zoom_start=13)
                folium.Marker(user_loc, popup="Your Location", icon=folium.Icon(color='red', icon='star', prefix='fa')).add_to(m)
                
                colors = {'Hospital': 'blue', 'Clinic': 'lightblue', 'Doctors': 'purple',
                         'Pharmacy': 'green', 'Police Station': 'darkblue', 'Fire Station': 'orange',
                         'ATM': 'gray', 'Embassy': 'pink', 'Tourist Office': 'lightgreen'}
                
                for _, row in df.iterrows():
                    popup = f"""<div style="width:220px;font-family:Inter,sans-serif;">
                        <h4 style="margin:0 0 8px 0;">{row['Name']}</h4>
                        <p style="margin:3px 0;font-size:0.85rem;"><b>Type:</b> {row['Type']}</p>
                        <p style="margin:3px 0;font-size:0.85rem;"><b>Distance:</b> {row['Distance_km']} km</p>
                        <p style="margin:3px 0;font-size:0.85rem;"><b>Phone:</b> {row['Phone']}</p>
                        <div style="margin-top:10px;">
                            <a href="{row['Google_Maps']}" target="_blank" 
                               style="background:#10b981;color:white;padding:6px 12px;text-decoration:none;
                                      border-radius:5px;margin-right:5px;display:inline-block;font-size:0.8rem;">Map</a>
                            <a href="{row['Directions']}" target="_blank" 
                               style="background:#3b82f6;color:white;padding:6px 12px;text-decoration:none;
                                      border-radius:5px;display:inline-block;font-size:0.8rem;">Directions</a>
                        </div>
                    </div>"""
                    folium.Marker([row['Latitude'], row['Longitude']], popup=folium.Popup(popup, max_width=250),
                                 tooltip=f"{row['Name']} ({row['Distance_km']} km)",
                                 icon=folium.Icon(color=colors.get(row['Type'], 'gray'), icon='info-sign')).add_to(m)
                
                folium.Circle(user_loc, radius=radius_km*1000, color='#3b82f6', fill=True, fillOpacity=0.1).add_to(m)
                folium_static(m, width=1200, height=500)
                
                # Download - Compact
                st.markdown('<div class="section-title">Download</div>', unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button("CSV", csv, f"services_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv", use_container_width=True)
                with col2:
                    txt = f"Services near {place_name}\n\n" + "\n".join([f"{i+1}. {r['Name']} ({r['Type']}) - {r['Distance_km']} km\n   {r['Phone']}\n   {r['Google_Maps']}" for i, r in df.head(30).iterrows()])
                    st.download_button("Text", txt, f"services_{datetime.now().strftime('%Y%m%d')}.txt", "text/plain", use_container_width=True)

# Footer - Compact
st.markdown('<div class="footer">Emergency Services Finder - India | Data: OpenStreetMap | For emergencies call helpline numbers</div>', unsafe_allow_html=True)
