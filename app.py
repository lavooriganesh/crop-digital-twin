import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from PIL import Image
import os

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Crop Digital Twin - Kalaburagi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# DASHBOARD DESIGN
# --------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
}
h1 {
    color: #176b3a;
    font-size: 30px !important;
}
h2, h3 {
    color: #244b35;
}
[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #dce8df;
    padding: 15px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# LOAD DATASETS
# --------------------------------------------------
@st.cache_data
def load_datasets():

    truth_path = (
        "ground_truth.csv"
        if os.path.exists("ground_truth.csv")
        else "data/ground_truth.csv"
    )

    twin_path = (
        "fused_digital_twin_data.csv"
        if os.path.exists("fused_digital_twin_data.csv")
        else "data/fused_digital_twin_data.csv"
    )

    if os.path.exists(truth_path):
        df_truth = pd.read_csv(truth_path)
    else:
        df_truth = pd.DataFrame({
            "date": [
                "2026-10-01", "2026-10-08",
                "2026-10-15", "2026-10-22",
                "2026-10-01", "2026-10-08",
                "2026-10-15", "2026-10-22"
            ],
            "field_id": [
                "Field-101", "Field-101",
                "Field-101", "Field-101",
                "Field-102", "Field-102",
                "Field-102", "Field-102"
            ],
            "soil_moisture_pct": [
                48, 41, 24, 18,
                46, 45, 44, 43
            ],
            "scout_vigour": [
                0.85, 0.80, 0.65, 0.52,
                0.79, 0.78, 0.77, 0.76
            ]
        })

    if os.path.exists(twin_path):
        df_twin = pd.read_csv(twin_path)
    else:
        df_twin = pd.DataFrame({
            "field_id": ["Field-101", "Field-102"],
            "crop": ["Maize", "Wheat"],
            "lat": [17.3297, 17.3450],
            "lon": [76.8343, 76.8520],
            "sat_ndvi": [0.42, 0.74],
            "soil_moisture_pct": [18.0, 43.0],
            "twin_status": [
                "Water Deficit Warning",
                "Optimal Growth"
            ],
            "twin_recommendation": [
                "Check soil moisture and irrigate if the reading is confirmed.",
                "Maintain the current irrigation schedule and continue monitoring."
            ],
            "twin_alert_level": ["warning", "success"]
        })

    # Check required columns
    defaults = {
        "field_id": "Field-101",
        "crop": "Crop",
        "lat": 17.3297,
        "lon": 76.8343,
        "sat_ndvi": 0.42,
        "soil_moisture_pct": 30.0,
        "twin_status": "Monitoring",
        "twin_recommendation": "Continue monitoring.",
        "twin_alert_level": "info"
    }

    for column, value in defaults.items():
        if column not in df_twin.columns:
            df_twin[column] = value

    for column, value in {
        "date": "2026-10-22",
        "field_id": "Field-101",
        "soil_moisture_pct": 30.0,
        "scout_vigour": 0.60
    }.items():
        if column not in df_truth.columns:
            df_truth[column] = value

    df_twin["lat"] = pd.to_numeric(df_twin["lat"], errors="coerce")
    df_twin["lon"] = pd.to_numeric(df_twin["lon"], errors="coerce")
    df_twin["sat_ndvi"] = pd.to_numeric(
        df_twin["sat_ndvi"], errors="coerce"
    )
    df_twin["soil_moisture_pct"] = pd.to_numeric(
        df_twin["soil_moisture_pct"], errors="coerce"
    )

    df_truth["date"] = pd.to_datetime(
        df_truth["date"], errors="coerce"
    )
    df_truth["soil_moisture_pct"] = pd.to_numeric(
        df_truth["soil_moisture_pct"], errors="coerce"
    )
    df_truth["scout_vigour"] = pd.to_numeric(
        df_truth["scout_vigour"], errors="coerce"
    )

    df_twin = df_twin.dropna(
        subset=["lat", "lon", "sat_ndvi", "soil_moisture_pct"]
    )

    df_truth = df_truth.dropna(subset=["date"])

    return df_truth, df_twin


# --------------------------------------------------
# SATELLITE NDVI VISUALIZATION
# --------------------------------------------------
@st.cache_data
def create_ndvi_image():

    red_path = next(
        (p for p in ["data/B04.tif", "B04.tif"]
         if os.path.exists(p)),
        None
    )

    nir_path = next(
        (p for p in ["data/B08.tif", "B08.tif"]
         if os.path.exists(p)),
        None
    )

    # Use real satellite bands when available
    if red_path and nir_path:
        try:
            import rasterio

            with rasterio.open(red_path) as src:
                red = src.read(1).astype("float32")
                red_nodata = src.nodata

            with rasterio.open(nir_path) as src:
                nir = src.read(1).astype("float32")
                nir_nodata = src.nodata

            if red.shape != nir.shape:
                return None, (
                    "The red and NIR images have different dimensions. "
                    "Align them before calculating NDVI."
                )

            denominator = nir + red

            ndvi = np.divide(
                nir - red,
                denominator,
                out=np.full_like(nir, np.nan),
                where=np.abs(denominator) > 0.000001
            )

            if red_nodata is not None:
                ndvi[red == red_nodata] = np.nan

            if nir_nodata is not None:
                ndvi[nir == nir_nodata] = np.nan

            ndvi[(ndvi < -1) | (ndvi > 1)] = np.nan

            valid = np.isfinite(ndvi)

            if not valid.any():
                return None, "No valid NDVI pixels were found."

            # Convert NDVI into a colored visualization
            scaled = np.clip(
                (np.nan_to_num(ndvi, nan=-1) + 1) * 127.5,
                0, 255
            ).astype("uint8")

            gray = Image.fromarray(scaled).resize((760, 420))

            values = np.asarray(gray).astype("float32") / 255.0

            rgb = np.zeros(
                (values.shape[0], values.shape[1], 3),
                dtype=np.uint8
            )

            rgb[..., 0] = (160 * (1 - values)).astype("uint8")
            rgb[..., 1] = (210 * values).astype("uint8")
            rgb[..., 2] = (70 * (1 - values)).astype("uint8")

            return Image.fromarray(rgb), (
                "NDVI calculated from the supplied red and NIR satellite bands."
            )

        except Exception as error:
            return None, f"Could not process satellite files: {error}"

    # Clearly labelled illustrative preview if no satellite files exist
    rng = np.random.default_rng(7)

    height, width = 420, 760

    yy, xx = np.mgrid[0:height, 0:width]

    crop_rows = np.sin((xx + yy * 0.45) / 17) > 0.15

    values = (
        0.48
        + 0.20 * np.sin(xx / 95)
        + 0.12 * np.cos(yy / 80)
        + rng.normal(0, 0.08, (height, width))
        + crop_rows * 0.18
    )

    values = np.clip(values, 0, 1)

    rgb = np.zeros((height, width, 3), dtype=np.uint8)

    rgb[..., 0] = (150 * (1 - values)).astype("uint8")
    rgb[..., 1] = (210 * values).astype("uint8")
    rgb[..., 2] = (55 * (1 - values)).astype("uint8")

    return Image.fromarray(rgb), (
        "Illustrative preview only. Add B04.tif and B08.tif "
        "to display NDVI calculated from satellite imagery."
    )


# --------------------------------------------------
# SATELLITE MAP
# --------------------------------------------------
def create_map(lat, lon, field_id, crop, moisture, ndvi, status):

    m = folium.Map(
        location=[lat, lon],
        zoom_start=17,
        control_scale=True,
        tiles=None
    )

    # Satellite imagery
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri World Imagery",
        name="Satellite View",
        overlay=False
    ).add_to(m)

    # Street map
    folium.TileLayer(
        "OpenStreetMap",
        name="Street Map",
        overlay=False
    ).add_to(m)

    # Approximate demonstration field boundary
    dlat = 0.0010
    dlon = 0.00125

    coordinates = [
        [lat - dlat, lon - dlon],
        [lat - dlat, lon + dlon],
        [lat + dlat, lon + dlon],
        [lat + dlat, lon - dlon]
    ]

    boundary_color = "#ff4444" if moisture < 25 else "#20c878"

    google_maps_url = (
        f"https://www.google.com/maps?q={lat},{lon}"
    )

    popup_html = f"""
    <b>{field_id} - {crop}</b><br>
    Status: {status}<br>
    NDVI: {ndvi:.2f}<br>
    Soil Moisture: {moisture:.1f}%<br>
    <a href="{google_maps_url}" target="_blank">
    Open in Google Maps
    </a>
    """

    folium.Polygon(
        locations=coordinates,
        color=boundary_color,
        weight=3,
        fill=True,
        fill_color=boundary_color,
        fill_opacity=0.10,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"{field_id} - {crop}"
    ).add_to(m)

    # Illustrative green crop rows
    for offset in np.linspace(-0.00082, 0.00082, 9):

        row_coordinates = [
            [lat - dlat * 0.78, lon + offset - 0.00012],
            [lat + dlat * 0.78, lon + offset + 0.00012]
        ]

        folium.PolyLine(
            row_coordinates,
            color="#39ff14" if moisture >= 25 else "#d6e600",
            weight=5,
            opacity=0.90,
            tooltip="Illustrative crop row"
        ).add_to(m)

    folium.Marker(
        [lat, lon],
        tooltip=f"{field_id} Sensor Node",
        popup=f"{field_id} Sensor Node",
        icon=folium.Icon(
            color="red" if moisture < 25 else "green",
            icon="info-sign"
        )
    ).add_to(m)

    folium.LayerControl().add_to(m)

    return m


# --------------------------------------------------
# LOAD PROJECT DATA
# --------------------------------------------------
df_truth, df_twin = load_datasets()

if df_twin.empty:
    st.error("No valid field data is available.")
    st.stop()


# --------------------------------------------------
# SIDEBAR FIELD SELECTION
# --------------------------------------------------
st.sidebar.title("📍 Select Farmland Parcel")

field_ids = df_twin["field_id"].astype(str).tolist()

selected_field_id = st.sidebar.selectbox(
    "Choose Field",
    field_ids,
    index=0
)

field = df_twin[
    df_twin["field_id"].astype(str) == selected_field_id
].iloc[0]

moisture = float(field["soil_moisture_pct"])
ndvi = float(field["sat_ndvi"])
status = str(field["twin_status"])
alert_level = str(field["twin_alert_level"]).lower()

st.sidebar.markdown("---")

st.sidebar.markdown(f"""
**Selected Field:** `{field['field_id']}`

**Crop Species:** `{field['crop']}`

**Soil Matrix:** `Black Cotton Soil (demo)`

**Latitude:** `{float(field['lat']):.5f}`

**Longitude:** `{float(field['lon']):.5f}`
""")

st.sidebar.caption(
    "Field boundaries and crop rows are illustrative."
)


# --------------------------------------------------
# MAIN DASHBOARD
# --------------------------------------------------
st.title("🌾 Crop Digital Twin Monitoring System")

st.caption(
    "Target Region: Kalaburagi, Karnataka | "
    "Space-to-Ground Agro-Hydrological Platform"
)


# --------------------------------------------------
# SUMMARY METRICS
# --------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Selected Field",
    str(field["field_id"])
)

c2.metric(
    "Crop Species",
    str(field["crop"])
)

c3.metric(
    "Soil Moisture",
    f"{moisture:.1f}%",
    delta="Low" if moisture < 25 else "Monitoring"
)

c4.metric(
    "Satellite NDVI",
    f"{ndvi:.2f}",
    delta="Low vegetation" if ndvi < 0.50 else "Vegetation detected"
)


# --------------------------------------------------
# DIAGNOSIS AND RECOMMENDATION
# --------------------------------------------------
st.subheader("System Diagnosis & Recommendation")

recommendation = str(field["twin_recommendation"])

if alert_level in ["warning", "danger", "critical"] or moisture < 25:

    st.warning(
        f"⚠️ **{status}** — {recommendation}"
    )

elif alert_level in ["success", "normal", "ok"]:

    st.success(
        f"✅ **{status}** — {recommendation}"
    )

else:

    st.info(
        f"ℹ️ **{status}** — {recommendation}"
    )

st.markdown("---")


# --------------------------------------------------
# MAP AND TIME SERIES GRAPH
# --------------------------------------------------
left, right = st.columns([1.1, 0.9], gap="large")

with left:

    st.subheader(
        f"1. Field Location Map ({field['field_id']} - {field['crop']})"
    )

    st.caption(
        "Satellite basemap with illustrative field boundary and crop rows."
    )

    field_map = create_map(
        lat=float(field["lat"]),
        lon=float(field["lon"]),
        field_id=str(field["field_id"]),
        crop=str(field["crop"]),
        moisture=moisture,
        ndvi=ndvi,
        status=status
    )

    st_folium(
        field_map,
        height=365,
        use_container_width=True,
        key=f"map_{selected_field_id}"
    )


with right:

    st.subheader("2. Dual Source Time Series Matching")

    history = df_truth[
        df_truth["field_id"].astype(str) == selected_field_id
    ].copy()

    history = history.sort_values("date")

    fig = go.Figure()

    if not history.empty:

        fig.add_trace(go.Scatter(
            x=history["date"],
            y=history["soil_moisture_pct"],
            name="Soil Moisture (%)",
            mode="lines+markers",
            line=dict(color="#3182ce", width=3)
        ))

        fig.add_trace(go.Scatter(
            x=history["date"],
            y=history["scout_vigour"] * 100,
            name="Canopy Vigour (%)",
            mode="lines+markers",
            line=dict(
                color="#38a169",
                width=3,
                dash="dot"
            )
        ))

    else:

        fig.add_annotation(
            text="No historical observations available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False
        )

    fig.update_layout(
        height=365,
        margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis_title="Observation Date",
        yaxis_title="Metric Scale",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified"
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#edf0f2"
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#edf0f2"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


st.markdown("---")


# --------------------------------------------------
# NDVI HEATMAP AND FIELD OBSERVATION LOG
# --------------------------------------------------
left2, right2 = st.columns([1.1, 0.9], gap="large")


with left2:

    st.subheader("3. NASA HLS Satellite NDVI Heatmap")

    ndvi_image, ndvi_message = create_ndvi_image()

    if ndvi_image is not None:

        st.image(
            ndvi_image,
            caption=f"NDVI visualization for {selected_field_id}",
            use_container_width=True
        )

    st.caption(ndvi_message)

    st.markdown("""
    **NDVI Formula:**

    NDVI = (NIR - Red) / (NIR + Red)

    Higher positive values often indicate denser green vegetation.
    """)


with right2:

    st.subheader("4. Field Observations & Twin State Log")

    history = df_truth[
        df_truth["field_id"].astype(str) == selected_field_id
    ].copy()

    history = history.sort_values("date")

    if not history.empty:

        log_df = pd.DataFrame({
            "Date": history["date"].dt.strftime("%Y-%m-%d"),
            "Parcel": history["field_id"].astype(str),
            "Soil Moisture": history[
                "soil_moisture_pct"
            ].map(lambda x: f"{x:.1f}%"),
            "Canopy Vigour": history[
                "scout_vigour"
            ].map(lambda x: f"{x * 100:.1f}%"),
            "Twin Status": [status] * len(history)
        })

    else:

        log_df = pd.DataFrame([{
            "Date": "No history",
            "Parcel": selected_field_id,
            "Soil Moisture": f"{moisture:.1f}%",
            "Canopy Vigour": "N/A",
            "Twin Status": status
        }])

    st.dataframe(
        log_df,
        use_container_width=True,
        height=260,
        hide_index=True
    )


# --------------------------------------------------
# REFERENCES
# --------------------------------------------------
with st.expander("🔗 Official State Alignment & Research References"):

    st.markdown("""
    **State Initiative Alignment:**  
    This dashboard demonstrates data-assisted crop monitoring
    and irrigation planning.

    **Satellite Data:**  
    NASA Harmonized Landsat Sentinel-2 (HLS) imagery can be
    processed to calculate vegetation indices.

    **NDVI Calculation:**  
    Red and near-infrared satellite bands are used to calculate NDVI.

    **Data Accuracy:**  
    Without B04.tif and B08.tif, the NDVI panel displays an
    illustrative preview rather than real satellite measurements.

    **Map Accuracy:**  
    The field boundary and green crop rows are illustrative.
    Verified GPS or GIS boundaries are required for accurate field mapping.

    **Recommendations:**  
    Confirm sensor readings and crop conditions before making
    irrigation or crop-treatment decisions.
    """)


st.markdown("---")

st.caption(
    "Crop Digital Twin Monitoring System | Kalaburagi, Karnataka"
)
