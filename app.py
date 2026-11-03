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
    page_title="Crop Digital Twin Monitoring System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------
@st.cache_data
def load_datasets():
    df_truth = pd.DataFrame({
        "date": ["2026-09-04", "2026-09-11", "2026-09-18", "2026-09-25", 
                 "2026-09-04", "2026-09-11", "2026-09-18", "2026-09-25"],
        "field_id": ["Field-101", "Field-101", "Field-101", "Field-101", 
                     "Field-102", "Field-102", "Field-102", "Field-102"],
        "soil_moisture_pct": [22.0, 20.0, 19.0, 18.0, 
                              46.0, 45.0, 44.0, 43.0],
        "scout_vigour": [0.55, 0.53, 0.50, 0.42, 
                         0.78, 0.76, 0.75, 0.74]
    })

    df_twin = pd.DataFrame({
        "field_id": ["Field-101", "Field-102"],
        "crop": ["Maize", "Wheat"],
        "lat": [17.1855, 17.2140],
        "lon": [76.9420, 76.9880],
        "sat_ndvi": [0.42, 0.74],
        "soil_moisture_pct": [18.0, 43.0],
        "twin_status": ["Water Deficit Warning", "Optimal Growth"],
        "twin_recommendation": [
            "Early irrigation required (root-zone stress detected)",
            "Crop canopy vigor and soil hydrology are balanced"
        ],
        "twin_alert_level": ["warning", "success"]
    })
    
    return df_truth, df_twin

@st.cache_data
def generate_botanical_canopy(crop_type, moisture_pct, ndvi_val):
    """Draws botanical canopy representation."""
    img_size = (380, 220)
    bg_color = (245, 240, 230) if moisture_pct < 25 else (225, 218, 200)
    img = Image.new("RGB", img_size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    for y in range(20, 220, 40):
        draw.line([(0, y), (380, y)], fill=(180, 160, 140), width=3)
        
    if moisture_pct < 25:
        leaf_color = (180, 160, 50)  
        num_leaves = 6
    else:
        leaf_color = (34, 139, 34)   
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
    """Builds interactive green forest and crop belt satellite map."""
    m = folium.Map(location=[lat, lon], zoom_start=17, tiles=None)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite Forest & Crop Belt',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    delta = 0.0015
    coords = [
        [lat - delta, lon - delta],
        [lat - delta, lon + delta],
        [lat + delta, lon + delta],
        [lat + delta, lon - delta]
    ]
    
    box_color = "#e53e3e" if moisture < 25 else "#16a34a"
    fill_color = "#fca5a5" if moisture < 25 else "#22c55e"
    
    # Direct Google Maps satellite URL matching your inspected view
    gmaps_url = f"https://www.google.com/maps/@{lat},{lon},18z/data=!3m1!1e3"
    
    folium.Polygon(
        locations=coords,
        color=box_color,
        weight=4,
        fill=True,
        fill_color=fill_color,
        fill_opacity=0.5,
        popup=f"<b>{field_name} ({crop_name})</b><br>Zone: Rural Green Forest & Farmland<br>Date: Sep 25, 2026<br>Status: {status}<br>Moisture: {moisture}%"
    ).add_to(m)
    
    folium.Marker(
        [lat, lon],
        popup=f"{field_name} Green Canopy Node",
        icon=folium.Icon(color="red" if moisture < 25 else "green", icon="info-sign")
    ).add_to(m)
    
    return m, gmaps_url

# ---------------------------------------------------------
# INTERFACE LAYOUT
# ---------------------------------------------------------
df_truth, df_twin = load_datasets()

st.sidebar.header("Select a Field")
field_list = df_twin["field_id"].tolist()
selected_field_id = st.sidebar.selectbox("Choose Field", field_list, index=0)

field_data = df_twin[df_twin["field_id"] == selected_field_id].iloc[0]

st.sidebar.markdown(f"""
**Selected Field:** `{field_data['field_id']}`[cite: 1, 2]  
**Crop Species:** `{field_data['crop']}`[cite: 1, 2]  
**Terrain:** `Rural Green Forest & Crop Belt`[cite: 1, 2]  
**Latitude:** `{field_data['lat']}`[cite: 1, 2]  
**Longitude:** `{field_data['lon']}`[cite: 1, 2]  
""")

# System Diagnosis & Recommendation Banner
st.markdown("### System Diagnosis & Recommendation (Sep 25, 2026)")
if field_data["twin_alert_level"] == "warning":
    st.error(f"⚠️ **ACTION NEEDED**: {field_data['twin_status']} ({field_data['twin_recommendation']})")
else:
    st.success(f"✅ **STATUS**: {field_data['twin_status']} ({field_data['twin_recommendation']})")

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    green_pct = 18 if field_data['field_id'] == 'Field-101' else 43
    st.markdown(f"#### 1. Field Location Map ({field_data['field_id']} - {field_data['crop']} Rows: {green_pct}% Green)")[cite: 1, 2]
    
    folium_map, direct_gmaps_link = build_map(
        lat=float(field_data["lat"]),
        lon=float(field_data["lon"]),
        field_name=field_data["field_id"],
        crop_name=field_data["crop"],
        status=field_data["twin_status"],
        moisture=float(field_data["soil_moisture_pct"]),
        ndvi=float(field_data["sat_ndvi"])
    )
    
    folium_static(folium_map, width=540, height=310)
    
    # Styled button linking directly to the real-time Google Maps satellite location
    st.markdown(
        f'<a href="{direct_gmaps_link}" target="_blank" style="display:block; text-align:center; background-color:#2563eb; color:white; padding:10px 20px; border-radius:5px; text-decoration:none; font-weight:bold; margin-top:10px;">🌍 Open Exact Field in Live Real-Time Google Maps</a>', 
        unsafe_allow_html=True
    )

with col_right:
    st.markdown("#### 2. Dual Source Time Series Matching (Sep, 2026)")[cite: 1, 2]
    
    field_history = df_truth[df_truth["field_id"] == selected_field_id]

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
            name="Canopy Health Score",
            mode="lines+markers",
            line=dict(color="#38a169", width=3, dash="dot")
        ))
    
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(title="Farmland Monitoring Timeline (Sep, 2026)"),
        yaxis=dict(title="Metric Scale"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

col_canopy, col_table = st.columns(2)

with col_canopy:
    st.markdown("#### 3. NASA HLS Satellite NDVI Heatmap (Sep 25)")[cite: 1, 2]
    if os.path.exists("data/ndvi_preview.png"):
        st.image("data/ndvi_preview.png", caption="NASA HLS Satellite NDVI Heatmap", use_container_width=True)
    else:
        canopy_img = generate_botanical_canopy(
            crop_type=field_data["crop"],
            moisture_pct=float(field_data["soil_moisture_pct"]),
            ndvi_val=float(field_data["sat_ndvi"])
        )
        st.image(canopy_img, caption=f"Simulated Canopy Structure for {field_data['field_id']}", use_container_width=True)

with col_table:
    st.markdown("#### 4. Field Observations & Twin State Log")[cite: 1, 2]
    log_df = pd.DataFrame({
        "Date": ["2026-09-04", "2026-09-11", "2026-09-18", "2026-09-25"],
        "Parcel": [field_data["field_id"]]*4,
        "Status": [field_data["twin_status"]]*4,
        "Moisture": [f"{float(field_data['soil_moisture_pct'])}%"]*4
    })
    st.dataframe(log_df, use_container_width=True, height=220)