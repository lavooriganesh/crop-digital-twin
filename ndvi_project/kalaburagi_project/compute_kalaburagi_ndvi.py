import os
import rasterio
from rasterio.enums import Resampling
import numpy as np

b4_file = os.path.join("data", "kalaburagi_B04.tif")
b8_file = os.path.join("data", "kalaburagi_B08.tif")
output_file = os.path.join("data", "kalaburagi_ndvi.tif")

print("Checking satellite band inputs on D: drive...")
if not os.path.exists(b4_file) or not os.path.exists(b8_file):
    raise FileNotFoundError(f"Missing band files in data/. Ensure {b4_file} and {b8_file} exist.")

print("Reading genuine Kalaburagi Sentinel-2 Level-2A surface reflectance...")

with rasterio.open(b4_file) as red_src:
    red_raw = red_src.read(1).astype("float32")
    profile = red_src.profile
    target_shape = red_raw.shape

with rasterio.open(b8_file) as nir_src:
    # Automatically align raster dimensions if download resolutions differed
    if nir_src.shape != target_shape:
        print(f"Aligning grids: Resampling B08 {nir_src.shape} to match B04 {target_shape}...")
        nir_raw = nir_src.read(
            1,
            out_shape=target_shape,
            resampling=Resampling.bilinear
        ).astype("float32")
    else:
        nir_raw = nir_src.read(1).astype("float32")

# 1. Mask out sensor no-data / border zero pixels
nodata_mask = (red_raw <= 0) & (nir_raw <= 0)

# 2. Rescale raw digital numbers to physical reflectance (0.0 to 1.0)
if np.nanmax(red_raw) > 10.0:
    red = red_raw / 10000.0
    nir = nir_raw / 10000.0
else:
    red = red_raw
    nir = nir_raw

# 3. Compute NDVI: (NIR - Red) / (NIR + Red)
np.seterr(divide="ignore", invalid="ignore")
denom = nir + red
ndvi = np.where((denom <= 0) | nodata_mask, np.nan, (nir - red) / denom)
ndvi = np.clip(ndvi, -1.0, 1.0)

# 4. Save Georeferenced NDVI GeoTIFF
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
print("     KALABURAGI GENUINE SENTINEL-2 NDVI METRICS     ")
print("=" * 55)
print(f"Total Measured Ground Pixels : {len(valid):,}")
print(f"Min Measured NDVI            : {np.nanmin(valid):.4f}")
print(f"Mean Regional NDVI           : {np.nanmean(valid):.4f}")
print(f"Max Measured NDVI            : {np.nanmax(valid):.4f}")
print("=" * 55)
print(f"[SUCCESS] Real NDVI GeoTIFF generated: {output_file}\n")