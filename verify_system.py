import os
import pandas as pd
import rasterio

def verify():
    print("=" * 60)
    print("       CROP DIGITAL TWIN SYSTEM INTEGRATION REPORT")
    print("=" * 60)

    # Box 2B Check
    if os.path.exists("data/ground_truth.csv"):
        df_gt = pd.read_csv("data/ground_truth.csv")
        print(f"[PASSED] Box 2B: ground_truth.csv ({len(df_gt)} records)")
    else:
        print("[FAILED] Box 2B: ground_truth.csv missing!")

    # Box 2A Check
    for b in ["data/B04.tif", "data/B08.tif"]:
        if os.path.exists(b):
            with rasterio.open(b) as s:
                print(f"[PASSED] Box 2A: {b} ({s.width}x{s.height} px)")
        else:
            print(f"[FAILED] Box 2A: {b} missing!")

    # Box 3 Check
    if os.path.exists("data/ndvi.tif") and os.path.exists("data/ndvi_preview.png"):
        print("[PASSED] Box 3: ndvi.tif and ndvi_preview.png generated")
    else:
        print("[FAILED] Box 3: NDVI outputs missing!")

    # Box 4 & 5 Check
    if os.path.exists("data/fused_digital_twin_data.csv"):
        df_fused = pd.read_csv("data/fused_digital_twin_data.csv")
        print(f"[PASSED] Box 4 & 5: fused_digital_twin_data.csv ({len(df_fused)} synchronized rows)")
    else:
        print("[FAILED] Box 4 & 5: Fused dataset missing!")

    print("=" * 60)

if __name__ == "__main__":
    verify()