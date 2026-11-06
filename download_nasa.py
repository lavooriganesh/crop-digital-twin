import earthaccess
import os
import shutil

def fetch_nasa_data():
    print("=== Step 1: NASA Earthdata Authentication ===")
    # Prompts for your NASA Earthdata credentials on the first run
    auth = earthaccess.login(strategy="interactive")
    if not auth.authenticated:
        print("[ERROR] Authentication failed. Check your Earthdata credentials.")
        return

    print("\n=== Step 2: Querying NASA HLS Sentinel-2 (HLSS30) Granules ===")
    bbox = (76.70, 17.20, 76.95, 17.45)    
    results = earthaccess.search_data(
        short_name="HLSS30",
        bounding_box=bbox,
        temporal=("2026-01-01", "2026-04-30"),
        cloud_cover=(0, 20),
        count=1
    )

    if not results:
        print("No scenes under 20% cloud cover. Searching broader range...")
        results = earthaccess.search_data(
            short_name="HLSS30",
            bounding_box=bbox,
            temporal=("2025-10-01", "2026-04-30"),
            cloud_cover=(0, 40),
            count=1
        )

    if not results:
        print("[ERROR] No granules found for the specified bounding box.")
        return

    print(f"[FOUND] Scene concept ID: {results[0]['meta']['concept-id']}")

    print("\n=== Step 3: Downloading Band 4 (Red) and Band 8A (NIR) ===")
    downloaded = earthaccess.download(results, "./temp_hls")

    b04_target = None
    b08_target = None

    for root, _, files in os.walk("./temp_hls"):
        for f in files:
            if "B04.tif" in f:
                b04_target = os.path.join(root, f)
            elif "B8A.tif" in f or "B08.tif" in f:
                b08_target = os.path.join(root, f)

    if b04_target and b08_target:
        shutil.copy(b04_target, "data/B04.tif")
        shutil.copy(b08_target, "data/B08.tif")
        print("\n[SUCCESS] Saved Band 4 to 'data/B04.tif'")
        print("[SUCCESS] Saved Band 8A to 'data/B08.tif'")
    else:
        print("\nFiles downloaded:", downloaded)
        print("Please check the './temp_hls' folder for the specific Red and NIR band filenames.")

    shutil.rmtree("./temp_hls", ignore_errors=True)

if __name__ == "__main__":
    fetch_nasa_data()