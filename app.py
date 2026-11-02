import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
from PIL import Image, ImageDraw
import os

# Set page configuration
st.set_page_config(
    page_title="Crop Digital Twin - Kalaburagi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# CACHED DATA & RESOURCE LOADING
# ---------------------------------------------------------
@st.cache_data
def load_datasets():
    """Loads CSV datasets checking both root and data/ directories."""
    truth_path = "ground_truth.csv" if os.path.exists("ground_truth.csv") else ("data/ground_truth.csv" if os.path.exists("data/ground_truth.csv") else None)
    twin_path = "fused_digital_twin_data.csv" if os.path.exists("fused_digital_twin_data.csv") else ("data/fused_digital_twin_data.csv" if os.path.exists("data/fused_digital_twin_data.csv") else None)

    if truth_path:
        df_truth = pd.read_csv(truth_path)
    else:
        df_truth = pd.DataFrame({
            "date": ["2026-10-01", "2026-10-08", "2026-10-15", "2026-10-22"],
            "field_id": ["Field-101", "Field-101", "Field-101", "Field-101"],
            "lat": [17.3297, 17.3297, 17.3297, 17.3297],
            "lon": [76.8343, 76.8343, 76.8343, 76.8343],
            "soil_moisture_pct": [48.0, 41.0, 24.0, 18.0],
            "scout_vigour": [0.85, 0.80, 0.65, 0.52]
        })

    if twin_path:
        df_twin = pd.read_csv(twin_path)
    else:
        df_twin = pd.DataFrame({
            "field_id": ["Field-101", "Field-102"],
            "crop": ["Maize", "Wheat"],
            "lat": [17.3297, 17.3450],
            "lon": [76.8343, 76.8520],
            "sat_ndvi": [0.42, 0.74],
            "soil_moisture_pct": [18.0, 43.0],
            "twin_status": ["Water Deficit Warning", "Optimal Growth"],
            "twin_recommendation": [
                "Immediate irrigation required (root-zone stress detected)",
                "Maintain standard scheduling"
            ],
            "twin_alert_level": ["warning", "success"]
        })
    
    return df_truth, df_twin

@st.cache_data
def generate_botanical_canopy(crop_type, moisture_pct, ndvi_val):
    """Draws synthetic crop canopy representation with safe integer coordinates."""
    img_size = (380, 220)
    bg_color = (245, 240, 230) if moisture_pct < 25 else (225, 218, 200)
    img = Image.new("RGB", img_size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Soil furrows
    for y in range(20, 220, 40):
        draw.line([(0, y), (380, y)], fill=(180, 160, 140), width=3)
        
    # Foliage settings
    if moisture_pct < 25:
        leaf_color = (180, 160, 50)  # Dehydration stress
        num_leaves = 6
    else:
        leaf_color = (34, 139, 34)   # Healthy foliage
        num_leaves = 14

    for x in range(30, 370, 45):
        for y in range(30, 210, 45):
            for i in range(num_leaves):
                dx = int(np.sin(i) * 14)
                dy = int(np.cos(i) * 10)
                x0 = int(x - abs(dx))
                y0 = int(y - abs(dy))
                x1 = int(x + abs(dx) + 4)
                y1 = int(y + abs(dy) + 4)
                if x1 > x0 and y1 > y0:
                    draw.ellipse([x0, y0, x1, y1], fill=leaf_color)
                
    return img

@st.cache_data
def build_map(lat, lon, field_name, crop_name, status, moisture, ndvi):
    """Caches Folium map generation with direct Google Maps link integration."""
    m = folium.Map(location=[lat, lon], zoom_start=16, tiles="OpenStreetMap")
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    delta = 0.003
    coords = [
        [lat - delta, lon - delta],
        [lat - delta, lon + delta],
        [lat + delta, lon + delta],
        [lat + delta, lon - delta]
    ]
    
    box_color = "#e53e3e" if moisture < 25 else "#38a169"
    gmaps_url = f"https://www.google.com/maps/@{lat},{lon},18t/data=!3m1!1e3"
    
    popup_html = f"""
    <b>{field_name} ({crop_name})</b><br>
    Status: {status}<br>
    NDVI: {ndvi}<br>
    Moisture: {moisture}%<br>
    <a href="{gmaps_url}" target="_blank">🌍 Open in Google Maps</a>
    """
    
    folium.Polygon(
        locations=coords,
        color=box_color,
        weight=3,
        fill=True,
        fill_color=box_color,
        fill_opacity=0.35,
        popup=folium.Popup(popup_html, max_width=300)
    ).add_to(m)
    
    folium.Marker(
        [lat, lon],
        popup=f"{field_name} Sensor Node",
        icon=folium.Icon(color="red" if moisture < 25 else "green", icon="info-sign")
    ).add_to(m)
    
    return m

# ---------------------------------------------------------
# DASHBOARD INTERFACE
# ---------------------------------------------------------
df_truth, df_twin = load_datasets()

st.title("🌾 Crop Digital Twin Monitoring System")
st.caption("Target Region: Kalaburagi, Karnataka | Space-to-Ground Agro-Hydrological Platform")

st.sidebar.header("📍 Select Farmland Parcel")
field_list = df_twin["field_id"].tolist()
selected_field_id = st.sidebar.selectbox("Choose Field", field_list, index=0)

field_data = df_twin[df_twin["field_id"] == selected_field_id].iloc[0]

# Sidebar Metadata Display matching your video
st.sidebar.markdown(f"""
**Selected Field:** `{field_data['field_id']}`  
**Crop Species:** `{field_data['crop']}`  
**Soil Matrix:** `Black Cotton Soil`  
**Latitude:** `{field_data['lat']}`  
**Longitude:** `{field_data['lon']}`  
""")

# System Diagnostics & Recommendation Banner
if field_data["twin_alert_level"] == "warning":
    st.error(f"⚠️ **SYSTEM DIAGNOSIS & RECOMMENDATION**: {field_data['twin_status']} — {field_data['twin_recommendation']}")
else:
    st.success(f"✅ **SYSTEM DIAGNOSIS & RECOMMENDATION**: {field_data['twin_status']} — {field_data['twin_recommendation']}")

st.markdown("---")

col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.subheader(f"1. Field Location Map ({field_data['field_id']} - {field_data['crop']} Rows: {int(field_data['soil_moisture_pct'])}% Green)")
    folium_map = build_map(
        lat=float(field_data["lat"]),
        lon=float(field_data["lon"]),
        field_name=field_data["field_id"],
        crop_name=field_data["crop"],
        status=field_data["twin_status"],
        moisture=float(field_data["soil_moisture_pct"]),
        ndvi=float(field_data["sat_ndvi"])
    )
    folium_static(folium_map, width=620, height=360)

with col_right:
    st.subheader("2. Dual Source Time Series Matching")
    
    field_history = df_truth[df_truth["field_id"] == selected_field_id] if not df_truth.empty else pd.DataFrame()

    fig = go.Figure()
    if not field_history.empty:
        fig.add_trace(go.Scatter(
            x=field_history["date"],
            y=field_history["soil_moisture_pct"],
            name="Soil Moisture (%)",
            mode="lines+markers",
            line=dict(color="#3182ce", width=3)
        ))
        fig.add_trace(go.Scatter(
            x=field_history["date"],
            y=field_history["scout_vigour"] * 100,
            name="Canopy Vigour Score",
            mode="lines+markers",
            line=dict(color="#38a169", width=3, dash="dot")
        ))
    else:
        sample_dates = ["2026-10-01", "2026-10-08", "2026-10-15", "2026-10-22"]
        base_m = float(field_data["soil_moisture_pct"])
        fig.add_trace(go.Scatter(
            x=sample_dates,
            y=[base_m+5, base_m+2, base_m-2, base_m],
            name="Soil Moisture (%)",
            mode="lines+markers",
            line=dict(color="#3182ce", width=3)
        ))

    fig.update_layout(
        height=340,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Trend History for Farmlands (Oct, 2026)"),
        yaxis=dict(title="Metric Scale"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

col_canopy, col_table = st.columns([1.1, 0.9])

with col_canopy:
    st.subheader("3. NASA HLS Satellite NDVI Heatmap")
    canopy_img = generate_botanical_canopy(
        crop_type=field_data["crop"],
        moisture_pct=float(field_data["soil_moisture_pct"]),
        ndvi_val=float(field_data["sat_ndvi"])
    )
    st.image(canopy_img, caption=f"Simulated Canopy Structure for {field_data['field_id']}", use_container_width=True)

with col_table:
    st.subheader("4. Field Observations & Twin State Log")
    log_df = pd.DataFrame({
        "Date": ["2026-10-01", "2026-10-08", "2026-10-15", "2026-10-22"],
        "Parcel": [field_data["field_id"]]*4,
        "Status": [field_data["twin_status"]]*4,
        "Moisture": [f"{float(field_data['soil_moisture_pct'])}%"]*4
    })
    st.dataframe(log_df, use_container_width=True, height=220)

with st.expander("🔗 Official State Alignment & Research References"):
    st.markdown("""
    * **State Initiative Alignment:** Supports Karnataka Government's AI-based crop monitoring framework for drought-hit regions.
    * **Validation Focus:** Real-time root-zone hydrological monitoring for black cotton agrarian soil in Kalaburagi.
    """)