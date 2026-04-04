from parcels import get_parcel_ids, search_owner


def main():
    print("Enter bounding box coordinates (lat_min, lon_min, lat_max, lon_max), comma-separated:")
    lat_min, lon_min, lat_max, lon_max = map(float, input().split(","))

    print("\nFetching cadastral parcel IDs...")
    ids = get_parcel_ids(lat_min, lon_min, lat_max, lon_max)
    print(f"Found {len(ids)} parcel(s) in the area.\n")

    print("Enter the name/surname to search for:")
    name = input().strip()

    print(f"\nSearching for '{name}'...")
    results = search_owner(ids, name)

    print(f"\nDone. Found {len(results)} matching possession sheet(s).")
    for r in results:
        print(f"  Parcel {r['parcel_id']} — {r['parcel_address']} — {r['possessors']}")


if __name__ == "__main__":
    main()
