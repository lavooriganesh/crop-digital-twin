import os
import numpy as np
import rasterio

raster_path = os.path.join("data", "multispectral.tif")
output_path = os.path.join("data", "NDVI_output.tif")

print("Opening satellite raster on D: drive...")

with rasterio.open(raster_path) as src:
    # Read Band 1 (Red) and Band 3 (NIR) as float32 for floating-point calculations
    red = src.read(1).astype("float32")
    nir = src.read(3).astype("float32")
    meta = src.meta.copy()

print(f"Raster dimensions: {red.shape[0]} rows x {red.shape[1]} columns")

# Compute NDVI: (NIR - Red) / (NIR + Red)
np.seterr(divide="ignore", invalid="ignore")
denominator = nir + red
ndvi = np.where(denominator == 0, np.nan, (nir - red) / denominator)
ndvi = np.clip(ndvi, -1.0, 1.0)

# Save NDVI GeoTIFF
meta.update(
    dtype=rasterio.float32,
    count=1,
    nodata=np.nan,
    driver="GTiff"
)

with rasterio.open(output_path, "w", **meta) as dst:
    dst.write(ndvi, 1)

print("\n--- Day 1 Verification ---")
valid_pixels = ndvi[~np.isnan(ndvi)]
print(f"Total Valid Pixels: {len(valid_pixels)}")
print(f"Min NDVI:  {np.nanmin(valid_pixels):.4f}")
print(f"Max NDVI:  {np.nanmax(valid_pixels):.4f}")
print(f"Mean NDVI: {np.nanmean(valid_pixels):.4f}")
print(f"\n[SUCCESS] Day 1 Deliverable created at: {output_path}")