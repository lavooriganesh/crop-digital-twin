import csv
import os

csv_file = os.path.join("data", "kalaburagi_ndvi_summary.csv")

data = [
    ["Region", "Sensor", "Acquisition Date", "Class Name", "NDVI Range", "Pixel Count", "Area Share (%)"],
    ["Kalaburagi", "Sentinel-2 L2A", "2026-01-05", "Water Bodies", "< 0.0", 104582, 1.77],
    ["Kalaburagi", "Sentinel-2 L2A", "2026-01-05", "Built-up / Bare Soil", "0.0 to 0.2", 436664, 7.39],
    ["Kalaburagi", "Sentinel-2 L2A", "2026-01-05", "Moderate Vegetation (Crops)", "0.2 to 0.5", 3618954, 61.29],
    ["Kalaburagi", "Sentinel-2 L2A", "2026-01-05", "Dense Canopy / Vigorous Biomass", ">= 0.5", 1744722, 29.55],
    ["Kalaburagi", "Sentinel-2 L2A", "2026-01-05", "Total Measured Area", "-1.0 to 1.0", 5904922, 100.00]
]

with open(csv_file, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(data)

print(f"[SUCCESS] Metrics exported to CSV: {csv_file}")