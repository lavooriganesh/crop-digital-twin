import pandas as pd

def run_digital_twin_fusion():
    print("=== Module 4: Spatial & Temporal Matching ===")
    df = pd.read_csv("data/ground_truth.csv")
    
    satellite_ndvi_map = {
        ("Field-101", "2026-10-01"): 0.81,
        ("Field-101", "2026-10-08"): 0.77,
        ("Field-101", "2026-10-15"): 0.53,
        ("Field-101", "2026-10-22"): 0.41,
        ("Field-102", "2026-10-01"): 0.83,
        ("Field-102", "2026-10-08"): 0.84,
        ("Field-102", "2026-10-15"): 0.81,
        ("Field-102", "2026-10-22"): 0.78,
    }
    df["sat_ndvi"] = [satellite_ndvi_map[(row["field_id"], row["date"])] for _, row in df.iterrows()]
    print(f"[OK] Synchronized {len(df)} field observations with satellite observations.")

    print("\n=== Module 5: Digital Twin State Rule Evaluation ===")
    def evaluate_state(row):
        ndvi = row["sat_ndvi"]
        moisture = row["soil_moisture_pct"]

        if ndvi >= 0.65 and moisture >= 35:
            return "Optimal Growth", "Crop canopy vigor and soil hydrology are balanced.", "success"
        elif moisture < 25 and ndvi >= 0.40:
            return "Water Deficit Warning", "Soil moisture critical (<25%). Early drought stress detected before leaf withering.", "warning"
        elif ndvi < 0.50 and moisture >= 35:
            return "Biotic Stress Anomaly", "Low canopy reflectance despite adequate soil moisture. Inspect for crop disease or pests.", "danger"
        else:
            return "Low Vigor / Harvesting", "Reduced active biomass detected.", "info"

    results = [evaluate_state(row) for _, row in df.iterrows()]
    df["twin_status"] = [r[0] for r in results]
    df["twin_recommendation"] = [r[1] for r in results]
    df["twin_alert_level"] = [r[2] for r in results]

    df.to_csv("data/fused_digital_twin_data.csv", index=False)
    print("[OK] Saved synchronized state data: data/fused_digital_twin_data.csv")

if __name__ == "__main__":
    run_digital_twin_fusion()