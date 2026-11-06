import os
import rasterio
import numpy as np

b4_file = os.path.join("data", "mangaluru_B04.tif")
b8_file = os.path.join("data", "mangaluru_B08.tif")
output_file = os.path.join("data", "mangaluru_ndvi.tif")

print("Reading real Sentinel-2 Level-2A satellite measurements...")

with rasterio.open(b4_file) as red_src:
    red_raw = red_src.read(1).astype("float32")
    profile = red_src.profile

with rasterio.open(b8_file) as nir_src:
    nir_raw = nir_src.read(1).astype("float32")

# Mask out orbital no-data margins (black border pixels where value is 0)
nodata_mask = (red_raw == 0) & (nir_raw == 0)

# Scale Level-2A 16-bit raw digital numbers to physical reflectance (0.0 to 1.0)
red = red_raw / 10000.0
nir = nir_raw / 10000.0

# Compute NDVI: (NIR - Red) / (NIR + Red)
np.seterr(divide="ignore", invalid="ignore")
denom = nir + red
ndvi = np.where((denom <= 0) | nodata_mask, np.nan, (nir - red) / denom)
ndvi = np.clip(ndvi, -1.0, 1.0)

profile.update(
    driver="GTiff",
    dtype=rasterio.float32,
    count=1,
    nodata=np.nan
)

with rasterio.open(output_file, "w", **profile) as dst:
    dst.write(ndvi, 1)

valid = ndvi[~np.isnan(ndvi)]

print("\n" + "=" * 55)
print("     MANGALURU GENUINE SENTINEL-2 NDVI METRICS     ")
print("=" * 55)
print(f"Total Measured Ground Pixels : {len(valid):,}")
print(f"Min Measured NDVI (Water)     : {np.nanmin(valid):.4f}")
print(f"Mean Regional NDVI            : {np.nanmean(valid):.4f}")
print(f"Max Measured NDVI (Canopy)    : {np.nanmax(valid):.4f}")
print("=" * 55)
print(f"[SUCCESS] Real NDVI GeoTIFF generated: {output_file}\n")
