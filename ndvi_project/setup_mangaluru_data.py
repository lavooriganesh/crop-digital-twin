import os
import rasterio
from rasterio.transform import from_bounds
import numpy as np

os.makedirs("data", exist_ok=True)

# Georeferenced bounding box for Mangaluru coastal belt (EPSG:4326)
west, south, east, north = 74.80, 12.82, 74.96, 12.98
rows, cols = 800, 800
transform = from_bounds(west, south, east, north, cols, rows)

x = np.linspace(0, 1, cols)
y = np.linspace(0, 1, rows)
xx, yy = np.meshgrid(x, y)

# Coastal profile: Arabian Sea on West, Land on East
coastline = 0.35 + 0.05 * np.sin(yy * 10)
water_mask = xx < coastline

# Netravati & Gurupura river mouths
river_mask = (np.abs(yy - 0.5 - 0.1 * np.sin(xx * 15)) < 0.02) & (xx >= coastline)
all_water = water_mask | river_mask

# Sentinel-2 L2A BOA Reflectance values (scaled 0 - 10000)
red = np.zeros((rows, cols), dtype=np.float32)
nir = np.zeros((rows, cols), dtype=np.float32)

# Water spectral signature: low reflection in red, near-zero in NIR
red[all_water] = 450.0 + np.random.normal(0, 20, np.sum(all_water))
nir[all_water] = 90.0 + np.random.normal(0, 10, np.sum(all_water))

# Land spectral signature: Mangaluru urban -> Agricultural -> Dense Ghats canopy
land_mask = ~all_water
dist = np.clip((xx[land_mask] - coastline[land_mask]) / (1.0 - coastline[land_mask]), 0, 1)

# Plants absorb Red (chlorophyll) and reflect NIR (mesophyll cell structure)
red[land_mask] = 1600.0 - 900.0 * dist + np.random.normal(0, 60, np.sum(land_mask))
nir[land_mask] = 2300.0 + 3800.0 * dist + np.random.normal(0, 90, np.sum(land_mask))

red = np.clip(red, 50.0, 8000.0)
nir = np.clip(nir, 50.0, 9000.0)

meta = {
    'driver': 'GTiff',
    'dtype': rasterio.float32,
    'nodata': -9999.0,
    'width': cols,
    'height': rows,
    'count': 1,
    'crs': 'EPSG:4326',
    'transform': transform
}

with rasterio.open("data/mangaluru_B04.tif", "w", **meta) as dst:
    dst.write(red, 1)

with rasterio.open("data/mangaluru_B08.tif", "w", **meta) as dst:
    dst.write(nir, 1)

print("[SUCCESS] Calibrated Mangaluru B04 and B08 GeoTIFFs created!")