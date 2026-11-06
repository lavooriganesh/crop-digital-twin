import pandas as pd

def generate_report():
    df = pd.read_csv("data/fused_digital_twin_data.csv")
    corr = df["sat_ndvi"].corr(df["scout_vigour"])
    
    report = f"""======================================================================
               CROP DIGITAL TWIN MONITORING SYSTEM
              Technical Specification & Execution Summary
======================================================================

1. DATA INGESTION:
   - Remote Sensing: NASA Harmonized Landsat-Sentinel-2 (HLSS30)
   - Bands: Band 4 (Red, 665 nm) and Band 8A (NIR, 865 nm)
   - Spatial Resolution: 30 meters
   - Ground Truth: In-situ soil moisture (%) and agronomic scout vigor ratings

2. PREPROCESSING & FORMULATION:
   - Vegetation Index: NDVI = (NIR - Red) / (NIR + Red)
   - Output Products: data/ndvi.tif (GeoTIFF) and data/ndvi_preview.png

3. DIGITAL TWIN LOGIC FUSION:
   - Model Calibration Fidelity (Pearson r): {corr * 100:.2f}%
   - Monitored Fields: {', '.join(df['field_id'].unique())}
   - Evaluation Rules:
       * Optimal Growth: NDVI >= 0.65 AND Moisture >= 35%
       * Water Deficit Warning: Moisture < 25% AND NDVI >= 0.40
       * Biotic Stress Anomaly: NDVI < 0.50 AND Moisture >= 35%

4. CURRENT STATUS OF MONITORED PARCELS:
"""
    for fid in df["field_id"].unique():
        sub = df[df["field_id"] == fid].iloc[-1]
        report += f"   * {fid} ({sub['crop']}): Status = '{sub['twin_status']}' | NDVI = {sub['sat_ndvi']} | Moisture = {sub['soil_moisture_pct']}%\n"

    report += "======================================================================\n"
    
    with open("PROJECT_SUMMARY.txt", "w") as f:
        f.write(report)
    
    print("[OK] Saved comprehensive report to 'PROJECT_SUMMARY.txt'")

if __name__ == "__main__":
    generate_report()