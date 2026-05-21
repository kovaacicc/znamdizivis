import json
import os
import requests

WFS_API = "https://api.uredjenazemlja.hr/services/inspire/cp/wfs"
PARCEL_INFO_URL = "https://oss.uredjenazemlja.hr/oss/public/cad/parcel-info"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Chrome/120.0.0.0 Safari/537.36)",
    "Referer": "https://oss.uredjenazemlja.hr/map",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "hr",
}


def get_parcel_ids(lat_min, lon_min, lat_max, lon_max):
    """
    Fetch all cadastral parcel IDs within a bounding box.

    Coordinates follow the WGS84 convention (EPSG:4326):
      lat_min/lon_min — bottom-left corner
      lat_max/lon_max — top-right corner

    Example: get_parcel_ids(45.82, 16.05, 45.83, 16.06)
    """
    all_ids = []
    fetched = 0
    total = -1

    while fetched != total:
        params = {
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAMES": "cp:CadastralParcel",
            "SRSNAME": "EPSG:4326",
            "BBOX": f"{lon_min},{lat_min},{lon_max},{lat_max},EPSG:4326",
            "COUNT": 1000,
            "STARTINDEX": fetched,
            "outputFormat": "application/json",
        }

        resp = requests.get(WFS_API, params=params, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

        for feature in data.get("features", []):
            all_ids.append(feature["id"].replace("CP.", ""))

        total = data.get("totalFeatures", 0)
        fetched += data.get("numberReturned", 0)
        print(f"  Fetching parcel IDs: {fetched} / {total}", end="\r", flush=True)

    print()

    return all_ids


def get_parcel_info(parcel_id):
    resp = requests.get(PARCEL_INFO_URL, params={"parcelId": parcel_id}, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def parse_parcel(data):
    return {
        "parcel_id": data.get("parcelId"),
        "cad_municipality_reg_num": data.get("cadMunicipalityRegNum"),
        "parcel_number": data.get("parcelNumber"),
        "parcel_address": data.get("address"),
        "parcel_parts": [p["name"] for p in data.get("parcelParts", [])],
        "possessors": [
            p["name"]
            for sheet in data.get("possessionSheets", [])
            for p in sheet.get("possessors", [])
        ],
    }


def _state_dir(name):
    """Return (and create) the per-person data directory under data/."""
    safe_name = name.strip().replace(" ", "_").lower()
    path = os.path.join("data", safe_name)
    os.makedirs(path, exist_ok=True)
    return path


def search_owner(parcel_ids, owner_name):
    """
    Search all parcel_ids for an owner matching owner_name (case-insensitive).

    Progress is persisted in data/<owner_name>/:
      checked.txt  — parcel IDs already inspected (no match)
      matches.json — parcels where a match was found

    Resuming after a crash or rate-limit just means re-running with the same
    inputs; already-checked parcels are skipped automatically.
    """
    state_dir = _state_dir(owner_name)
    checked_path = os.path.join(state_dir, "checked.txt")
    matches_path = os.path.join(state_dir, "matches.json")
    raw_path = os.path.join(state_dir, "raw.json")

    checked = set()
    if os.path.exists(checked_path):
        with open(checked_path) as f:
            checked = {line.strip() for line in f if line.strip()}

    results = []
    if os.path.exists(matches_path):
        with open(matches_path) as f:
            results = json.load(f)

    raw_results = []
    if os.path.exists(raw_path):
        with open(raw_path) as f:
            raw_results = json.load(f)

    remaining = [pid for pid in parcel_ids if pid not in checked]
    skipped = len(parcel_ids) - len(remaining)
    if skipped:
        print(f"  Skipping {skipped} already-checked parcel(s), {len(remaining)} remaining")

    for i, parcel_id in enumerate(remaining):
        print(f"  Checking {i + 1}/{len(remaining)} — parcelId: {parcel_id}  ", end="\r", flush=True)
        data = get_parcel_info(parcel_id)
        parsed = parse_parcel(data)

        if any(owner_name.upper() in p.upper() for p in parsed["possessors"]):
            print(f"  ✓ Found '{owner_name}' on parcel {parcel_id}!{' ' * 20}")
            results.append(parsed)
            raw_results.append(data)
            with open(matches_path, "w") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            with open(raw_path, "w") as f:
                json.dump(raw_results, f, ensure_ascii=False, indent=2)
        else:
            with open(checked_path, "a") as f:
                f.write(f"{parcel_id}\n")

    return results
