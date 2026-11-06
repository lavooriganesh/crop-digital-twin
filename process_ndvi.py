import os
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.enums import Resampling


def compute_and_save_ndvi(
    red_path="data/B04.tif",
    nir_path="data/B08.tif",
    out_tif_path="data/ndvi.tif",
    out_png_path="data/ndvi_preview.png"
):
    print("=== Calculating Satellite NDVI ===")

    os.makedirs("data", exist_ok=True)

    with rasterio.open(red_path) as red_src:
        red = red_src.read(1).astype("float32")
        red_nodata = red_src.nodata
        red_profile = red_src.profile.copy()
        red_transform = red_src.transform
        red_crs = red_src.crs

    with rasterio.open(nir_path) as nir_src:
        nir = nir_src.read(1).astype("float32")
        nir_nodata = nir_src.nodata
        nir_transform = nir_src.transform
        nir_crs = nir_src.crs

    if red.shape != nir.shape:
        raise ValueError("B04 and B08 dimensions do not match.")

    if red_transform != nir_transform or red_crs != nir_crs:
        raise ValueError("B04 and B08 are not aligned to the same grid.")

    valid = np.isfinite(red) & np.isfinite(nir)

    if red_nodata is not None:
        valid &= red != red_nodata

    if nir_nodata is not None:
        valid &= nir != nir_nodata

    denominator = nir + red
    valid &= denominator > 0

    ndvi = np.full(red.shape, -9999.0, dtype="float32")

    ndvi[valid] = (
        (nir[valid] - red[valid]) / denominator[valid]
    )

    valid &= (ndvi >= -1) & (ndvi <= 1)
    ndvi[~valid] = -9999.0

    profile = red_profile.copy()
    profile.update(
        dtype="float32",
        count=1,
        nodata=-9999.0,
        compress="lzw"
    )

    with rasterio.open(out_tif_path, "w", **profile) as dst:
        dst.write(ndvi, 1)

    print("[OK] NDVI GeoTIFF saved:", out_tif_path)

    display_ndvi = np.ma.masked_equal(ndvi, -9999.0)

    fig, ax = plt.subplots(figsize=(9, 7))

    cmap = plt.colormaps["RdYlGn"].copy()
    cmap.set_bad("#eeeeee")

    image = ax.imshow(
        display_ndvi,
        cmap=cmap,
        vmin=-1,
        vmax=1
    )

    fig.colorbar(image, ax=ax, label="NDVI")
    ax.set_title("NASA HLS Satellite NDVI - Kalaburagi")
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_png_path, dpi=150)
    plt.close(fig)

    values = ndvi[ndvi != -9999.0]

    if values.size == 0:
        raise ValueError("No valid NDVI pixels found.")

    print("[OK] NDVI preview saved:", out_png_path)
    print("Valid pixels:", values.size)
    print("Mean NDVI:", round(float(values.mean()), 3))
    print("Minimum NDVI:", round(float(values.min()), 3))
    print("Maximum NDVI:", round(float(values.max()), 3))


if __name__ == "__main__":
    compute_and_save_ndvi()