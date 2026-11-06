import os
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

ndvi_path = os.path.join("data", "kalaburagi_ndvi.tif")
output_png = os.path.join("data", "kalaburagi_ndvi_analysis.png")

if not os.path.exists(ndvi_path):
    raise FileNotFoundError(f"Missing {ndvi_path}. Run compute_kalaburagi_ndvi.py first.")

print("Loading real Kalaburagi NDVI GeoTIFF from D: drive...")

with rasterio.open(ndvi_path) as src:
    ndvi = src.read(1)

valid_mask = ~np.isnan(ndvi)
valid_ndvi = ndvi[valid_mask]
total_pixels = len(valid_ndvi)

# Scientific Ecological Thresholds
water_count = np.sum(valid_ndvi < 0.0)
builtup_count = np.sum((valid_ndvi >= 0.0) & (valid_ndvi < 0.2))
mod_veg_count = np.sum((valid_ndvi >= 0.2) & (valid_ndvi < 0.5))
dense_veg_count = np.sum(valid_ndvi >= 0.5)

print("\n" + "=" * 58)
print("     KALABURAGI REGIONAL LAND COVER BREAKDOWN    ")
print("=" * 58)
print(f"Water Bodies (NDVI < 0)        : {water_count:9,d} pixels ({water_count/total_pixels*100:6.2f}%)")
print(f"Built-up / Bare (0.0 to 0.2)   : {builtup_count:9,d} pixels ({builtup_count/total_pixels*100:6.2f}%)")
print(f"Moderate Veg (0.2 to 0.5)      : {mod_veg_count:9,d} pixels ({mod_veg_count/total_pixels*100:6.2f}%)")
print(f"Dense Canopy (NDVI >= 0.5)     : {dense_veg_count:9,d} pixels ({dense_veg_count/total_pixels*100:6.2f}%)")
print("-" * 58)
print(f"Total Measured Ground Area     : {total_pixels:9,d} pixels (100.00%)")
print("=" * 58)

# Build thematic classification array
classified = np.full(ndvi.shape, np.nan, dtype=np.float32)
classified[(ndvi < 0.0) & valid_mask] = 0
classified[(ndvi >= 0.0) & (ndvi < 0.2) & valid_mask] = 1
classified[(ndvi >= 0.2) & (ndvi < 0.5) & valid_mask] = 2
classified[(ndvi >= 0.5) & valid_mask] = 3

fig, axes = plt.subplots(1, 2, figsize=(16, 8), dpi=200)

# Panel 1: Continuous NDVI Heatmap
im1 = axes[0].imshow(ndvi, cmap="RdYlGn", vmin=-0.2, vmax=0.8)
axes[0].set_title("Kalaburagi Continuous NDVI Map\n(Sentinel-2 L2A Surface Reflectance - Jan 2026)", fontsize=12, fontweight="bold")
axes[0].axis("off")
cbar1 = fig.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04)
cbar1.set_label("NDVI Index Value", fontsize=10)

# Panel 2: Thematic Discrete Classification
cmap_disc = ListedColormap(["#1f77b4", "#d95f02", "#e6ab02", "#1b9e77"])
norm_disc = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap_disc.N)
im2 = axes[1].imshow(classified, cmap=cmap_disc, norm=norm_disc)
axes[1].set_title("Kalaburagi Land Cover Classification Map\n(Ecological Thresholds)", fontsize=12, fontweight="bold")
axes[1].axis("off")

cbar2 = fig.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04, ticks=[0, 1, 2, 3])
cbar2.ax.set_yticklabels([
    f"Water ({water_count/total_pixels*100:.1f}%)",
    f"Built-up/Bare ({builtup_count/total_pixels*100:.1f}%)",
    f"Moderate Veg ({mod_veg_count/total_pixels*100:.1f}%)",
    f"Dense Canopy ({dense_veg_count/total_pixels*100:.1f}%)"
], fontsize=9)

plt.tight_layout()
plt.savefig(output_png, bbox_inches="tight")
plt.close()

print(f"\n[SUCCESS] Final Report generated at: {output_png}\n")